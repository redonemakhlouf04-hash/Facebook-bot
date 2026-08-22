#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
import os
import json
import random
import sys
from datetime import datetime
from colorama import Fore, Style, init

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
import schedule

init(autoreset=True)

# إعداد السجلات
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# قراءة الملفات
try:
    with open('accounts.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    with open('posts_content.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    with open('comments.json', 'r', encoding='utf-8') as f:
        comments = json.load(f)
    with open('keywords.json', 'r', encoding='utf-8') as f:
        keywords = json.load(f)
except Exception as e:
    logger.error(f"❌ خطأ في تحميل الملفات: {e}")
    sys.exit(1)

class FacebookBot:
    """البوت الرئيسي"""
    
    def __init__(self, account, config, posts, comments, keywords):
        self.account = account
        self.config = config
        self.posts = posts
        self.comments = comments
        self.keywords = keywords
        self.driver = None
        self.wait = None
    
    def get_proxy(self):
        """الحصول على proxy"""
        proxy = self.config['proxies'][self.account['id'] % len(self.config['proxies'])]
        return f"http://{proxy['ip']}:{proxy['port']}"
    
    def start_browser(self):
        """بدء المتصفح"""
        logger.info(f"🌐 [حساب #{self.account['id']}] بدء المتصفح...")
        
        try:
            proxy = self.get_proxy()
            options = webdriver.ChromeOptions()
            options.add_argument(f'--proxy-server={proxy}')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            self.driver = uc.Chrome(options=options, headless=False)
            self.wait = WebDriverWait(self.driver, 20)
            
            logger.info(f"✅ تم بدء المتصفح")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False
    
    def load_cookies(self):
        """تحميل الكوكيز"""
        logger.info(f"🍪 تحميل الكوكيز...")
        
        try:
            self.driver.get("https://www.facebook.com")
            time.sleep(3)
            
            cookies = [
                {"name": "c_user", "value": self.account['c_user'], "domain": ".facebook.com"},
                {"name": "xs", "value": self.account['xs'], "domain": ".facebook.com"},
                {"name": "datr", "value": self.account['datr'], "domain": ".facebook.com"},
                {"name": "sb", "value": self.account['sb'], "domain": ".facebook.com"},
            ]
            
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            
            self.driver.refresh()
            time.sleep(3)
            
            logger.info(f"✅ تم تحميل الكوكيز")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False
    
    def is_logged_in(self):
        """التحقق من تسجيل الدخول"""
        try:
            self.driver.get("https://www.facebook.com/")
            time.sleep(2)
            self.driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Home"]')
            logger.info(f"✅ مسجل دخول")
            return True
        except:
            logger.warning(f"⚠️ لم يتم تسجيل الدخول")
            return False
    
    def post_to_profile(self):
        """نشر على البروفايل"""
        logger.info(f"📱 نشر على البروفايل...")
        
        try:
            self.driver.get("https://www.facebook.com")
            time.sleep(2)
            
            post_box = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@contenteditable='true' and @role='textbox']")
                )
            )
            
            post_content = random.choice(self.posts['posts'])['content']
            post_box.send_keys(post_content)
            
            time.sleep(2)
            
            publish_button = self.driver.find_element(
                By.XPATH,
                "//div[@role='button' and contains(text(), 'Post')]"
            )
            publish_button.click()
            
            logger.info(f"✅ تم النشر")
            time.sleep(3)
            return True
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False
    
    def find_groups(self):
        """البحث عن جروبات"""
        logger.info(f"🔍 البحث عن جروبات...")
        
        groups = []
        try:
            keyword = random.choice(self.keywords['keywords'])
            search_url = f"https://www.facebook.com/search/groups/?q={keyword}"
            self.driver.get(search_url)
            time.sleep(3)
            
            # تمرير الصفحة
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
            
            group_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/groups/')]")
            
            for link in group_links[:50]:
                try:
                    url = link.get_attribute('href')
                    name = link.text
                    if url and name:
                        groups.append({'name': name[:50], 'url': url})
                except:
                    pass
            
            logger.info(f"📊 وجد {len(groups)} جروب")
            return groups
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return []
    
    def join_and_post_group(self, group):
        """الانضمام والنشر في جروب"""
        try:
            self.driver.get(group['url'])
            time.sleep(2)
            
            # الانضمام
            try:
                join_button = self.driver.find_element(
                    By.XPATH,
                    "//div[@role='button' and contains(text(), 'Join')]"
                )
                join_button.click()
                time.sleep(2)
            except:
                pass
            
            # النشر
            post_box = self.wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@contenteditable='true' and @role='textbox']")
                )
            )
            
            post_content = random.choice(self.posts['group_posts'])
            post_box.send_keys(post_content)
            
            time.sleep(1)
            
            publish_button = self.driver.find_element(
                By.XPATH,
                "//div[@role='button' and contains(text(), 'Post')]"
            )
            publish_button.click()
            
            logger.info(f"✅ نشر في: {group['name']}")
            time.sleep(2)
            return True
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False
    
    def send_friend_request(self, profile_url):
        """إرسال طلب صداقة"""
        try:
            self.driver.get(profile_url)
            time.sleep(2)
            
            add_friend = self.driver.find_element(
                By.XPATH,
                "//div[@role='button' and contains(text(), 'Add Friend')]"
            )
            add_friend.click()
            
            logger.info(f"👥 طلب صداقة")
            time.sleep(2)
            return True
        except:
            return False
    
    def like_posts(self):
        """إعطاء لايكات"""
        logger.info(f"👍 إعطاء لايكات...")
        
        try:
            self.driver.get("https://www.facebook.com/")
            time.sleep(2)
            
            for _ in range(5):
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(1)
                
                try:
                    like_button = self.driver.find_element(
                        By.XPATH,
                        "//svg[@aria-label='Like']"
                    )
                    like_button.click()
                    logger.info(f"👍 لايك")
                    time.sleep(1)
                except:
                    pass
            
            return True
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            return False
    
    def run(self):
        """تشغيل السير الكامل"""
        logger.info("\n" + "="*60)
        logger.info(f"🚀 [حساب #{self.account['id']}] بدء السير")
        logger.info("="*60)
        
        try:
            # 1. بدء المتصفح
            if not self.start_browser():
                return False
            
            # 2. تحميل الكوكيز
            if not self.load_cookies():
                self.driver.quit()
                return False
            
            # 3. التحقق من تسجيل الدخول
            if not self.is_logged_in():
                self.driver.quit()
                return False
            
            # 4. نشر على البروفايل
            self.post_to_profile()
            time.sleep(5)
            
            # 5. إعطاء لايكات
            if self.config['settings']['enable_likes']:
                self.like_posts()
            time.sleep(5)
            
            # 6. البحث عن جروبات والنشر
            groups = self.find_groups()
            
            for idx, group in enumerate(groups[:50], 1):
                logger.info(f"📍 [{idx}/50] {group['name']}")
                self.join_and_post_group(group)
                
                delay = random.uniform(
                    self.config['settings']['min_delay'],
                    self.config['settings']['max_delay']
                )
                time.sleep(delay)
            
            # 7. إرسال طلبات صداقة
            if self.config['settings']['enable_friend_requests']:
                logger.info(f"👥 إرسال طلبات صداقة...")
                
                for i in range(25):
                    keyword = random.choice(self.keywords['keywords'])
                    self.driver.get(f"https://www.facebook.com/search/people/?q={keyword}")
                    time.sleep(2)
                    
                    try:
                        profile_links = self.driver.find_elements(
                            By.XPATH,
                            "//a[contains(@href, '/profile.php?id=')]"
                        )
                        
                        for link in profile_links[:1]:
                            url = link.get_attribute('href')
                            self.send_friend_request(url)
                            time.sleep(random.uniform(5, 15))
                            break
                    except:
                        pass
            
            # إغلاق المتصفح
            self.driver.quit()
            
            logger.info("\n" + "="*60)
            logger.info(f"✅ انتهى السير بنجاح!")
            logger.info("="*60 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            if self.driver:
                self.driver.quit()
            return False

# جدولة النشر
def run_posting():
    """تشغيل النشر لجميع الحسابات"""
    logger.info("🔄 تشغيل جميع الحسابات...")
    
    for account in config['accounts']:
        if account['enabled']:
            bot = FacebookBot(account, config, posts, comments, keywords)
            bot.run()
            
            # تأخير بين الحسابات
            delay = random.uniform(300, 600)
            logger.info(f"⏳ تأخير {delay:.0f} ثانية...")
            time.sleep(delay)

def main():
    """الدالة الرئيسية"""
    
    logger.info("\n" + Fore.MAGENTA + "="*60)
    logger.info(Fore.MAGENTA + "🤖 Facebook Auto Bot - 24/7")
    logger.info(Fore.MAGENTA + "="*60)
    logger.info(Fore.CYAN + f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(Fore.CYAN + f"📊 الحسابات: {len(config['accounts'])}")
    logger.info(Fore.CYAN + f"🔗 الـ Proxies: {len(config['proxies'])}")
    logger.info(Fore.MAGENTA + "="*60 + "\n")
    
    try:
        # جدولة النشر
        for time_str in config['settings']['posting_times']:
            schedule.every().day.at(time_str).do(run_posting)
            logger.info(f"✅ نشر في {time_str}")
        
        logger.info(Fore.YELLOW + "\n⏰ البرنامج يعمل 24/7\n")
        
        # حلقة الجدولة
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info(Fore.RED + "\n🛑 تم الإيقاف")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ خطأ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
