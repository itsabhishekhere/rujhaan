import asyncio
import json
from playwright.async_api import async_playwright

import argparse

def clean_search_volume(volume_text):
    if not volume_text:
        return ""
    # Take the first line (e.g., "500K+")
    volume_part = volume_text.split('\n')[0].strip()
    
    multiplier = 1
    if 'K' in volume_part:
        multiplier = 1000
        volume_part = volume_part.replace('K', '')
    elif 'M' in volume_part:
        multiplier = 1000000
        volume_part = volume_part.replace('M', '')
        
    # Handle '+'
    has_plus = '+' in volume_part
    volume_part = volume_part.replace('+', '').replace(',', '')
    
    try:
        number = int(float(volume_part) * multiplier)
        return f"{number}+" if has_plus else str(number)
    except ValueError:
        return volume_part

async def main(geo="IN", fetch_news=False):
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = f"https://trends.google.com/trending?geo={geo}"
        print(f"Navigating to Google Trends ({geo})...")
        await page.goto(url)
        
        # Wait for at least one row to be visible
        row_selector = "tr.enOdEe-wZVHld-xMbwt.UlR2Yc"
        try:
            await page.wait_for_selector(row_selector, timeout=10000)
        except Exception as e:
            print(f"Timeout waiting for rows: {e}")
            await browser.close()
            return
        
        all_trends = []
        page_num = 1
        
        try:
            while True:
                print(f"Processing page {page_num}...")
                
                # Wait a bit for any animations or data updates
                await page.wait_for_timeout(2000)
                
                # Get all rows
                rows = await page.locator(row_selector).all()
                
                print(f"Found {len(rows)} rows on this page.")
                
                if len(rows) == 0:
                    print("Warning: No rows found, but selector was waited for.")
                
                # We need to iterate by index because clicking rows might stale the locator list
                for i in range(len(rows)):
                    try:
                        # Re-query rows to avoid stale element errors
                        current_rows = await page.locator(row_selector).all()
                        if i >= len(current_rows):
                            break
                        row = current_rows[i]
                        
                        # Term: 2nd column, first div
                        term_element = row.locator("td:nth-child(2) > div").first
                        term = await term_element.inner_text()
                        
                        # Search Volume: 3rd column, first div
                        volume_element = row.locator("td:nth-child(3) > div").first
                        volume = clean_search_volume(await volume_element.inner_text())
                        
                        # Started At: 4th column, div with class 'vdw3Ld'
                        time_element = row.locator("td:nth-child(4) > div").first
                        started_at = await time_element.inner_text()
                        
                        # Trend Breakdown (Related Queries): 5th column, spans
                        related_elements = row.locator("td:nth-child(5) span").all()
                        related_queries = []
                        for el in await related_elements:
                            text = await el.inner_text()
                            if text and not text.startswith("+") and text not in ["Explore", "query_stats"] and text not in related_queries:
                                related_queries.append(text)
                        
                        news_articles = []
                        if fetch_news:
                            # Click the row to open side panel
                            # We click the term element to be safe
                            await term_element.click()
                            
                            # Wait for side panel news to appear
                            # Selector for news container: a.xZCHj
                            try:
                                # Wait a bit for panel to open
                                await page.wait_for_timeout(2000)
                                
                                # Check if news items exist
                                # The class xZCHj seemed correct, but let's try a more generic approach if it fails.
                                # News items are usually links with an image and text in the side panel.
                                # Let's try to find them by looking for links that contain "hours ago" or similar text, 
                                # or just stick to the class if we are sure.
                                # Let's try the class again but with a wait.
                                try:
                                    await page.wait_for_selector("a.xZCHj", timeout=5000)
                                except:
                                    print(f"No news items found for {term} (selector timeout).")
                                
                                news_items = await page.locator("a.xZCHj").all()
                                
                                for item in news_items:
                                    url = await item.get_attribute("href")
                                    # Title is usually the first block of text
                                    title = await item.locator("div > div").first.inner_text()
                                    # Source/Time is usually the second block
                                    try:
                                        source_time = await item.locator("div > div").nth(1).inner_text()
                                    except:
                                        source_time = "Unknown"
                                    
                                    news_articles.append({
                                        "title": title,
                                        "url": url,
                                        "source_time": source_time
                                    })
                                    
                                # Close the panel
                                # Try pressing Escape first as it's most robust
                                await page.keyboard.press("Escape")
                                await page.wait_for_timeout(500)
                                
                            except Exception as e:
                                print(f"Error fetching news for {term}: {e}")
                                await page.keyboard.press("Escape")

                        if term:
                            trend_data = {
                                "term": term,
                                "search_volume": volume,
                                "started_at": started_at,
                                "related_queries": related_queries
                            }
                            if fetch_news:
                                trend_data["news"] = news_articles
                                
                            all_trends.append(trend_data)
                            
                    except Exception as e:
                        print(f"Error extracting data from row {i}: {e}")
                
                # Check for "Next" button
                next_button = page.locator("button[aria-label='Go to next page']")
                
                if await next_button.count() > 0 and await next_button.is_enabled():
                    await next_button.click()
                    page_num += 1
                else:
                    print("No more pages or 'Next' button disabled.")
                    break
        
        except KeyboardInterrupt:
            print("\nScript interrupted by user.")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
        finally:
            print(f"Total trends fetched: {len(all_trends)}")
            
            # Save to file
            filename = f"trending_terms_{geo}.json"
            with open(filename, "w") as f:
                json.dump(all_trends, f, indent=2, ensure_ascii=False)
                
            print(f"Saved to {filename}")
            
            await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Google Trends data.")
    parser.add_argument("--geo", type=str, default="IN", help="Two-letter country code (e.g., IN, US, GB). Default is IN.")
    parser.add_argument("--news", action="store_true", help="Fetch news articles for each trend (slower).")
    args = parser.parse_args()
    
    asyncio.run(main(geo=args.geo, fetch_news=args.news))
