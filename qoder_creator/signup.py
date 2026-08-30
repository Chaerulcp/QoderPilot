"""
QoderPilot - Signup Manager
Full signup flow: temp mail â†’ form â†’ captcha (local slider) â†’ OTP â†’ account created â†’ PAT.
"""

import asyncio
import random
import time
from typing import Optional, Dict, Any
from urllib.parse import urlsplit

from playwright.async_api import async_playwright, Page
from rich.console import Console
from rich.text import Text

from .config import QODER_BASE, ACCOUNTS_FILE, DATA_DIR, SIGNUP_RETRY
from .utils import write_log, generate_password, save_jsonl
from .tempmail import TempikClient, TempMailError
from .proxy import ProxyPool
from .stealth import create_stealth_context, launch_stealth_browser
from .captcha import solve_slider_local
from .pat import PATManager

# OTP email delivery tuning: when the email has not arrived within
# OTP_TOTAL_WAIT_SECONDS, the whole signup attempt is closed and restarted from
# scratch (up to SIGNUP_RETRY + 1 attempts in total).
OTP_TOTAL_WAIT_SECONDS = 240
OTP_POLL_INTERVAL_SECONDS = 5
OTP_RETRY_DELAY_SECONDS = 5


class _OtpTimeout(Exception):
    """Internal signal: the OTP email never arrived; safe to restart signup."""


class SignupManager:
    """Handle Qoder signup + PAT creation."""

    def __init__(
        self,
        proxy_pool: ProxyPool = None,
        headless: bool = True,
        console: Console = None,
    ):
        self.proxy_pool = proxy_pool
        self.headless = headless
        self.console = console or Console()

    async def create_account(
        self,
        idx: int = 0,
        proxy: Dict[str, str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Full signup flow for one account.
        Returns: {email, password, pat, ...} or None on failure.

        When the OTP email never arrives, the whole signup is restarted from
        scratch (fresh temp email, password, and browser) up to
        SIGNUP_RETRY + 1 attempts in total.
        """
        if proxy is None and self.proxy_pool:
            proxy = self.proxy_pool.next()

        max_attempts = SIGNUP_RETRY + 1
        for attempt in range(1, max_attempts + 1):
            try:
                return await self._create_account_once(idx, attempt, proxy)
            except _OtpTimeout:
                if attempt >= max_attempts:
                    self.console.print("  :x: [red]OTP timeout pada semua percobaan.[/]")
                    write_log(
                        f"[{idx}] OTP timeout after {max_attempts} attempts; giving up",
                        "ERROR",
                    )
                    return None
                self.console.print(
                    f"  [yellow][*] OTP timeout; mengulang signup dari awal "
                    f"({attempt + 1}/{max_attempts})...[/]"
                )
                write_log(
                    f"[{idx}] OTP timeout on attempt {attempt}; restarting signup "
                    f"from scratch ({attempt + 1}/{max_attempts})",
                    "WARNING",
                )
                await asyncio.sleep(OTP_RETRY_DELAY_SECONDS)
        return None

    async def _create_account_once(
        self,
        idx: int,
        attempt: int,
        proxy: Dict[str, str] = None,
    ) -> Optional[Dict[str, Any]]:
        """One signup attempt; raises _OtpTimeout when the OTP email never arrives."""
        c = self.console

        # Step 1: Get temp email
        c.print(f"\n[bold cyan]Account #{idx} (percobaan {attempt}/{SIGNUP_RETRY + 1})[/]")
        c.print("  :mailbox: Getting temp email...")
        tempmail = TempikClient(proxy=proxy)
        try:
            email = tempmail.create_inbox()
        except TempMailError as exc:
            c.print(f"  [red]Temp mail setup failed:[/] {exc}")
            write_log(f"[{idx}] Temp mail setup failed: {exc}", "ERROR")
            return None
        password = generate_password()

        c.print(f"  :envelope: Email: [cyan]{email}[/]")
        c.print(f"  :key: Password: [yellow]{password}[/]")
        write_log(f"[{idx}] Signup start (attempt {attempt}): {email}", "INFO")

        try:
            async with async_playwright() as p:
                # Step 2: Launch browser
                c.print("  :rocket: Launching browser...")
                browser = await launch_stealth_browser(p, proxy, self.headless)
                context = await create_stealth_context(browser, proxy)
                page = await context.new_page()
                page.on("response", lambda response: self._log_signup_response(response, idx))

                # Step 3: Open signup page
                c.print("  :globe_with_meridians: Opening signup page...")
                await page.goto(
                    f"{QODER_BASE}/users/sign-up",
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                await page.wait_for_timeout(5000)

                # Step 4: Fill form (name + email)
                c.print("  :pencil: Filling signup form...")
                try:
                    await page.fill("#basic_firstName", "User")
                    await page.fill("#basic_lastName", "Dev")
                    await page.fill("#basic_email", email)
                except Exception as e:
                    write_log(f"[{idx}] Form fill error: {e}", "ERROR")
                    c.print(f"  :x: [red]Form fill failed: {e}[/]")
                    await context.close()
                    await browser.close()
                    return None

                # Checkbox
                cb = await page.query_selector("input[type=checkbox]")
                if cb:
                    try:
                        await cb.check(force=True)
                    except Exception:
                        pass

                # Click Continue
                await self._click(page, ['button:has-text("Continue")'])
                await page.wait_for_timeout(4000)

                # Step 5: Fill password
                c.print("  :lock: Filling password...")
                pw = await page.query_selector("#basic_password")
                if pw:
                    try:
                        await pw.click(force=True)
                        await page.keyboard.type(password, delay=20)
                    except Exception:
                        pass
                await self._click(page, ['button:has-text("Continue")'])
                await page.wait_for_timeout(4000)

                # Step 6: Solve captcha
                c.print("  :puzzle_piece: Solving captcha...")
                await self._click(page, [
                    "#aliyunCaptcha-captcha-body",
                    'button:has-text("Click to verify")',
                ])
                await page.wait_for_timeout(3000)

                solved = await solve_slider_local(
                    page,
                    max_attempts=5,
                    console=c,
                    stop_check=lambda: SignupManager._otp_form_visible(page),
                )
                if not solved:
                    # The local solver can miss a server-side success (the form
                    # may have been submitted while a drag was still running).
                    # Only fail when the OTP form is truly absent.
                    solved = await self._otp_form_visible(page)
                    if solved:
                        write_log(
                            f"[{idx}] Captcha solver reported failure but the OTP form is visible; continuing",
                            "WARNING",
                        )
                if not solved:
                    c.print("  :x: [red]Captcha failed![/]")
                    write_log(f"[{idx}] Captcha failed for {email}", "ERROR")
                    await context.close()
                    await browser.close()
                    return None

                c.print("  :white_check_mark: [green]Captcha solved![/]")

                # A local slider match is not proof that Qoder accepted the
                # verification or sent an email. Wait for the server-driven
                # OTP form before polling the mailbox.
                otp_ready, otp_error = await self._wait_for_otp_step(page)
                if not otp_ready:
                    screenshot = DATA_DIR / f"signup-otp-not-triggered-{idx}.png"
                    try:
                        await page.screenshot(path=str(screenshot), full_page=True)
                    except Exception as exc:
                        write_log(f"[{idx}] Unable to save signup screenshot: {exc}", "WARNING")

                    detail = otp_error or "Qoder did not display the OTP form"
                    c.print(f"  :x: [red]OTP request was not accepted:[/] {detail}")
                    c.print(f"  [dim]Diagnostic screenshot: {screenshot}[/]")
                    write_log(f"[{idx}] OTP step not reached for {email}: {detail}", "ERROR")
                    await context.close()
                    await browser.close()
                    return None

                # Step 7: Wait for OTP
                c.print("  :white_check_mark: [green]Qoder accepted the OTP request.[/]")
                c.print(
                    f"  :inbox_tray: Waiting for OTP email (up to {OTP_TOTAL_WAIT_SECONDS} seconds)..."
                )
                messages = await tempmail.wait_for_messages(
                    email,
                    max_wait=OTP_TOTAL_WAIT_SECONDS,
                    interval=OTP_POLL_INTERVAL_SECONDS,
                )

                if not messages:
                    c.print("  :x: [red]No messages received — OTP timeout![/]")
                    write_log(f"[{idx}] OTP timeout for {email} (attempt {attempt})", "ERROR")
                    await context.close()
                    await browser.close()
                    raise _OtpTimeout(email)

                otp = tempmail.extract_otp(messages)
                if not otp:
                    c.print("  :x: [red]Could not extract OTP![/]")
                    write_log(f"[{idx}] OTP extraction failed for {email}", "ERROR")
                    await context.close()
                    await browser.close()
                    return None

                c.print(f"  :incoming_envelope: OTP: [bold green]{otp}[/]")

                # Step 8: Fill OTP
                c.print("  :keyboard: Filling OTP...")
                otp_inputs = await page.query_selector_all('input.ant-otp-input')
                if len(otp_inputs) >= 6:
                    await otp_inputs[0].click()
                    await page.wait_for_timeout(200)
                    await page.keyboard.type(otp, delay=80)
                    await page.wait_for_timeout(1500)
                else:
                    all_inputs = await page.query_selector_all('input:not([type="hidden"])')
                    if all_inputs:
                        await all_inputs[0].click()
                        await page.keyboard.type(otp, delay=80)
                    else:
                        await page.keyboard.type(otp, delay=80)

                await self._click(page, [
                    'button:has-text("Create account")',
                    'button:has-text("Verify")',
                    'button[type="submit"]',
                ])
                await page.wait_for_timeout(8000)

                # Step 9: Check result
                current_url = page.url
                if "download" in current_url or "dashboard" in current_url:
                    c.print("  :white_check_mark: [bold green]Account created![/]")
                else:
                    c.print("  :warning: [yellow]Account may be pending...[/]")

                # Step 10: Create PAT
                c.print("  :shield: Creating PAT...")
                pat_response = await PATManager.create(page, "farm")
                pat_token = PATManager.extract_token(pat_response)
                pat_valid = PATManager.is_valid(pat_response)

                if pat_valid:
                    c.print(f"  :white_check_mark: [green]PAT valid! ({len(pat_token)} chars)[/]")
                else:
                    c.print(f"  :x: [yellow]PAT invalid: {pat_response.get('status')}[/]")

                await context.close()
                await browser.close()

                # Step 11: Build result
                result = {
                    "email": email,
                    "password": password,
                    "pat_token": pat_token,
                    "pat_valid": pat_valid,
                    "pat_response": pat_response,
                    "url": current_url,
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }

                save_jsonl(ACCOUNTS_FILE, result)
                write_log(f"[{idx}] Signup complete: {email} (PAT valid={pat_valid})", "SUCCESS")

                return result

        except _OtpTimeout:
            raise
        except Exception as e:
            write_log(f"[{idx}] Signup error: {e}", "ERROR")
            c.print(f"  :x: [red]Error: {e}[/]")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    async def _click(page: Page, selectors: list) -> Optional[str]:
        """Click first visible selector."""
        for sel in selectors:
            try:
                el = await page.query_selector(sel)
                if el and await el.is_visible():
                    await el.click()
                    return sel
            except Exception:
                continue
        return None

    @staticmethod
    async def _otp_form_visible(page: Page) -> bool:
        """Return True when any Qoder OTP input is currently visible."""
        try:
            otp_inputs = await page.query_selector_all("input.ant-otp-input")
            for otp_input in otp_inputs:
                if await otp_input.is_visible():
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    async def _wait_for_otp_step(page: Page, timeout: int = 15000) -> tuple[bool, str]:
        """Wait until Qoder confirms signup by displaying the OTP form."""
        deadline = time.monotonic() + (timeout / 1000)
        last_error = ""

        while time.monotonic() < deadline:
            if await SignupManager._otp_form_visible(page):
                return True, ""

            current_error = await SignupManager._visible_signup_error(page)
            if current_error:
                last_error = current_error
                normalized = current_error.lower()
                terminal_errors = (
                    "too frequently",
                    "rate limit",
                    "abnormal mailbox",
                    "cannot sign up",
                    "cannot signup",
                    "registration failed",
                    "email config",
                )
                if any(message in normalized for message in terminal_errors):
                    return False, current_error

            await page.wait_for_timeout(250)

        if last_error:
            return False, last_error
        return False, f"OTP form did not appear (current page: {page.url})"

    @staticmethod
    async def _visible_signup_error(page: Page) -> str:
        """Return a visible Qoder form error without exposing page contents."""
        selectors = (
            ".ant-message-error",
            ".ant-form-item-explain-error",
            "[role='alert']",
        )
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    if not await element.is_visible():
                        continue
                    text = " ".join((await element.inner_text()).split())
                    if text:
                        return text[:300]
            except Exception:
                continue
        return ""

    @staticmethod
    def _log_signup_response(response: Any, idx: int) -> None:
        """Log Qoder API response metadata without credentials or bodies."""
        try:
            request = response.request
            if request.resource_type not in {"xhr", "fetch"}:
                return
            if request.method.upper() not in {"POST", "PUT", "PATCH"}:
                return

            parsed = urlsplit(response.url)
            host = (parsed.hostname or "").lower()
            if not (
                host == "qoder.com"
                or host.endswith(".qoder.com")
                or host.endswith(".qoder.sh")
            ):
                return

            level = "INFO" if response.ok else "WARNING"
            write_log(
                f"[{idx}] Qoder signup request {request.method.upper()} "
                f"{parsed.path}: HTTP {response.status}",
                level,
            )
        except Exception:
            return


async def create_accounts(
    count: int = 1,
    proxy_pool: ProxyPool = None,
    headless: bool = True,
    delay: int = 5,
    console: Console = None,
) -> list:
    """Create multiple accounts (legacy â€” use SignupManager directly)."""
    manager = SignupManager(proxy_pool, headless, console)
    results = []

    for i in range(count):
        result = await manager.create_account(i + 1)
        if result:
            results.append(result)

        if i < count - 1:
            wait = delay + random.randint(0, 5)
            c = console or Console()
            c.print(f"  :hourglass: Waiting [yellow]{wait}s[/] before next account...")
            await asyncio.sleep(wait)

    ok = [r for r in results if r and r.get("pat_valid")]
    c = console or Console()
    c.print()
    if ok:
        c.print(f"[green]:tada: Done: {len(ok)}/{count} accounts with valid PAT[/]")
    else:
        c.print(f"[red]:x: All {count} accounts failed[/]")
    c.print(f"[dim]Saved to: {ACCOUNTS_FILE}[/]")

    return results
