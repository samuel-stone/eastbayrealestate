from playwright.sync_api import Page, TimeoutError

def safe_click_next(page: Page, timeout_ms: int = 15000) -> bool:
    """
    Safely clicks the 'Next >' pagination button, waiting for any overlay 
    loading masks to disappear first so the click isn't intercepted.
    """
    next_btn = page.locator("a:has-text('Next >')").first
    
    if not next_btn.is_visible():
        return False

    # Wait out any lingering global loading masks (common in Accela portals)
    mask = page.locator("#divGlobalLoadingMask")
    try:
        if mask.is_visible():
            mask.wait_for(state="hidden", timeout=timeout_ms)
    except TimeoutError:
        # Fallback short pause if mask stays visible
        page.wait_for_timeout(1000)

    next_btn.click(timeout=timeout_ms)
    return True