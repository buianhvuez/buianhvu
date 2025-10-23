(function () {

  function log(...args) { try { console.log("[Autofill]", ...args); } catch { } }
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));
  log("Script Injected! Waiting 5 seconds before starting...");

  function waitForElement(selector, textOrRegex, timeout = 7000) {
      return new Promise((resolve, reject) => {
          let intervalTime = 250; elapsedTime = 0;
          const interval = setInterval(() => {
              elapsedTime += intervalTime;
              let elements = Array.from(document.querySelectorAll(selector));
              if (textOrRegex) {
                  const regex = (typeof textOrRegex === 'string') ? new RegExp(`^${textOrRegex.trim()}$`, 'i') : textOrRegex;
                  elements = elements.filter(el => (el.textContent && regex.test(el.textContent.trim())) || (el.innerText && regex.test(el.innerText.trim())));
              }
              if (elements.length > 0) {
                  const visibleElement = elements.find(el => {
                      try {
                          const style = window.getComputedStyle(el); const rect = el.getBoundingClientRect();
                          return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0' && rect.width > 0 && rect.height > 0;
                      } catch (e) { return false; }
                  });
                  if (visibleElement) { clearInterval(interval); resolve(visibleElement); }
              }
              if (elapsedTime >= timeout) { clearInterval(interval); reject(`Không tìm thấy element ('${selector}' / '${textOrRegex}') sau ${timeout}ms`); }
          }, intervalTime);
      });
  }

  // === HÀM TẮT POPUP ĐÃ CẬP NHẬT VÀ CẢI THIỆN ===
  async function closeRegisterPagePopups() {
      let closedSomething = false;
      let attempts = 0;
      const maxAttempts = 3;

      // Lặp lại việc tắt popup nhiều lần để đảm bảo
      while (attempts < maxAttempts && !closedSomething) {
          attempts++;
          log(`Register Page: Popup closing attempt ${attempts}/${maxAttempts}`);

          // --- 1. Thử tắt Popup 1 ("TIN TỨC MỚI NHẤT") với nhiều selector hơn ---
          try {
              log("Register Page: Checking for Popup 1 (backdrop or [translate='Common_Closed'])...");
              
              // Thử nhiều selector cho backdrop
              const backdropSelectors = [
                  '.cdk-overlay-backdrop',
                  '.modal-backdrop',
                  '.popup-backdrop',
                  '.overlay-backdrop',
                  '[class*="backdrop"]',
                  '[class*="overlay"]'
              ];
              
              let backdropFound = false;
              for (const selector of backdropSelectors) {
                  try {
                      const backdrop = await waitForElement(selector, null, 1000);
                      log(`Register Page: Found backdrop with selector '${selector}'. Clicking...`);
                      backdrop.click();
                      closedSomething = true;
                      backdropFound = true;
                      await sleep(500);
                      break;
                  } catch (e) {
                      // Tiếp tục thử selector tiếp theo
                  }
              }

              if (!backdropFound) {
                  // Thử các nút đóng khác nhau
                  const closeButtonSelectors = [
                      'button[translate="Common_Closed"]',
                      'button[class*="close"]',
                      'button[class*="Close"]',
                      '.close',
                      '.fa-times',
                      '.fa-close',
                      '[aria-label*="close" i]',
                      '[aria-label*="đóng" i]',
                      'button:contains("Đóng")',
                      'button:contains("Close")',
                      'button:contains("×")',
                      'button:contains("X")'
                  ];

                  for (const selector of closeButtonSelectors) {
                      try {
                          const closeButton = await waitForElement(selector, null, 1000);
                          log(`Register Page: Found close button with selector '${selector}'. Clicking...`);
                          closeButton.click();
                          closedSomething = true;
                          await sleep(500);
                          break;
                      } catch (e) {
                          // Tiếp tục thử selector tiếp theo
                      }
                  }
              }
          } catch (eFirstAttempt) {
              log("Register Page: Popup 1 elements not found.");
          }

          // --- 2. Thử tắt Popup 2 ("THÔNG BÁO") với nhiều selector hơn ---
          try {
              log("Register Page: Checking for Popup 2 (announcement popup)...");
              
              // Thử nhiều selector cho popup thông báo
              const announcementSelectors = [
                  'button[translate="Announcement_GotIt"]',
                  'button[class*="announcement"]',
                  'button[class*="Announcement"]',
                  'button:contains("Got it")',
                  'button:contains("Đã hiểu")',
                  'button:contains("OK")',
                  'button:contains("Đồng ý")',
                  'button:contains("Tôi hiểu")',
                  'button:contains("Xác nhận")',
                  'button:contains("Confirm")'
              ];

              let announcementFound = false;
              for (const selector of announcementSelectors) {
                  try {
                      const gotItButton = await waitForElement(selector, null, 2000);
                      log(`Register Page: Found announcement button with selector '${selector}'. Clicking...`);
                      gotItButton.click();
                      closedSomething = true;
                      announcementFound = true;
                      await sleep(500);
                      break;
                  } catch (e) {
                      // Tiếp tục thử selector tiếp theo
                  }
              }

              if (!announcementFound) {
                  // Thử các nút X khác nhau
                  const xButtonSelectors = [
                      '.fa-times',
                      '.fa-close',
                      'span.close',
                      'button.close',
                      '[class*="close"]',
                      '[class*="Close"]',
                      'button[aria-label*="close" i]',
                      'button[aria-label*="đóng" i]',
                      'button:contains("×")',
                      'button:contains("X")',
                      'span:contains("×")',
                      'span:contains("X")'
                  ];

                  for (const selector of xButtonSelectors) {
                      try {
                          const xButton = await waitForElement(selector, null, 1500);
                          log(`Register Page: Found X button with selector '${selector}'. Clicking...`);
                          xButton.click();
                          closedSomething = true;
                          await sleep(500);
                          break;
                      } catch (e) {
                          // Tiếp tục thử selector tiếp theo
                      }
                  }
              }
          } catch (eSecondAttempt) {
              log("Register Page: Popup 2 elements not found.");
          }

          // --- 3. Thử tắt các popup khác có thể xuất hiện ---
          try {
              log("Register Page: Checking for other popups...");
              
              // Thử tắt các modal/popup chung
              const generalPopupSelectors = [
                  '.modal',
                  '.popup',
                  '.overlay',
                  '.dialog',
                  '[role="dialog"]',
                  '[role="alertdialog"]',
                  '.notification',
                  '.alert',
                  '.toast'
              ];

              for (const selector of generalPopupSelectors) {
                  try {
                      const popup = await waitForElement(selector, null, 1000);
                      // Kiểm tra xem popup có visible không
                      const style = window.getComputedStyle(popup);
                      const rect = popup.getBoundingClientRect();
                      if (style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0) {
                          // Tìm nút đóng trong popup này
                          const closeButtons = popup.querySelectorAll('button, [class*="close"], [aria-label*="close" i], [aria-label*="đóng" i]');
                          for (const btn of closeButtons) {
                              try {
                                  log(`Register Page: Found close button in popup '${selector}'. Clicking...`);
                                  btn.click();
                                  closedSomething = true;
                                  await sleep(500);
                                  break;
                              } catch (e) {
                                  // Tiếp tục thử nút tiếp theo
                              }
                          }
                      }
                  } catch (e) {
                      // Tiếp tục thử selector tiếp theo
                  }
              }
          } catch (eThirdAttempt) {
              log("Register Page: Other popups not found.");
          }

          // Nếu đã tắt được gì đó, dừng lại
          if (closedSomething) {
              log(`Register Page: Successfully closed popups in attempt ${attempts}`);
              break;
          }

          // Nếu chưa tắt được gì, chờ một chút rồi thử lại
          if (attempts < maxAttempts) {
              log(`Register Page: No popups found in attempt ${attempts}, waiting before retry...`);
              await sleep(1000);
          }
      }

      log(`Register Page: Popup closing attempts finished. Total attempts: ${attempts}, Closed something: ${closedSomething}`);
      return closedSomething;
  }

  // === LOGIC AUTOFILL GỐC (GIỮ NGUYÊN) ===
  const host = location.hostname.replace(/^www\./, '').toLowerCase();

  function findInput({ selectors = [], placeholders = [], labelKeywords = [], scope = document } = {}) {
        for (const sel of selectors) {
      try { const el = scope.querySelector(sel); if (el) return el; } catch { }
    }
    if (placeholders.length) {
      for (const el of scope.querySelectorAll('input, textarea')) {
        const ph = (el.getAttribute('placeholder') || '').toLowerCase();
        for (const kw of placeholders) if (ph.includes(kw.toLowerCase())) return el;
      }
    }
    if (labelKeywords.length) {
      for (const lb of scope.querySelectorAll('label')) {
        const txt = (lb.textContent || '').toLowerCase();
        for (const kw of labelKeywords) {
          if (txt.includes(kw.toLowerCase())) {
            const forId = lb.getAttribute('for');
            if (forId) {
              const linked = document.getElementById(forId);
              if (linked && /^(INPUT|TEXTAREA)$/.test(linked.tagName)) return linked;
            }
            const group = lb.closest('.form-group, .input-group, .row, .group, .form-item') || lb.parentElement;
            if (group) {
              const inGroup = group.querySelector('input, textarea');
              if (inGroup) return inGroup;
            }
            let sib = lb.nextElementSibling;
            while (sib) {
              const cand = sib.querySelector?.('input, textarea') || (sib.matches?.('input,textarea') ? sib : null);
              if (cand) return cand;
              sib = sib.nextElementSibling;
            }
          }
        }
      }
    }
    return null;
  }

  function fill(el, val, name) {
        if (!el || val == null || val === '') return false;
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set;
    if (setter) setter.call(el, val); else el.value = val;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur',  { bubbles: true }));
    log(">>> filled:", name || el.name || el.id || el.getAttribute('formcontrolname') || el.placeholder);
    return true;
  }

  // ====== MAP ĐẶC THÙ ======
  const SITE = {
        "m.8nohu.vip": {
      user: { selectors: ['input[name="Username"]', 'input[id*="user"]', 'input[name*="user"]', 'input[type="email"]', 'input[type="text"]'], placeholders: ['tên tài khoản', 'tai khoan', 'username', 'user'] },
      pass: { selectors: ['input[name="Password"]', 'input[id*="pass"]', 'input[type="password"]'], placeholders: ['mật khẩu', 'mat khau', 'password'] },
      repass: { selectors: ['input[name="ConfirmPassword"]', 'input[name*="confirm"]', 'input[id*="confirm"]'], placeholders: ['xác nhận mật khẩu', 'xac nhan mat khau', 'nhập lại', 'nhap lai', 're-password', 'confirm'] }
    },
    "m.tt88.zip": tt88Selectors(),
    "tt88.zip": tt88Selectors(),
    "1tt88.vip": tt88Selectors(),
    "m.mmoo.team": {
      user: { selectors: ['input[name="Username"]', 'input[name*="user"]', 'input[id*="user"]', 'input[type="email"]', 'input[type="text"]'], placeholders: ['tên tài khoản', 'tai khoan', 'username', 'user'] },
      pass: { selectors: ['input[name="Password"]', 'input[type="password"]', 'input[id*="pass"]'], placeholders: ['mật khẩu', 'mat khau', 'password'] },
      repass: { selectors: ['input[name="ConfirmPassword"]', 'input[name*="confirm"]', 'input[id*="confirm"]'], placeholders: ['xác nhận mật khẩu', 'xac nhan mat khau', 'nhập lại', 'nhap lai', 'confirm', 're-password'] }
    },
    "1go99.vip": {
      user: { selectors: ['input[name="Username"]', 'input[name="LoginName"]', 'input[name="Account"]', 'input[name*="user"]', 'input[name*="account"]', 'input[name*="login"]', 'input[id*="user"]', 'input[type="email"]', 'input[type="tel"]', 'input[type="text"]'] },
      pass: { selectors: ['input[name="Password"]', 'input[name*="Pwd"]', 'input[name*="Pass"]', 'input[id*="pwd"]', 'input[id*="pass"]', 'input[type="password"]'] },
      repass: { selectors: ['input[name="ConfirmPassword"]', 'input[name*="ConfirmPwd"]', 'input[name*="RePwd"]', 'input[name*="RePass"]', 'input[name*="Again"]', 'input[id*="confirm"]'] }
    },
    "789p1.vip": {
      user: { selectors: ['input[name="Username"]', 'input[name="Account"]', 'input[name*="user"]', 'input[name*="account"]', 'input[name*="login"]', 'input[id*="user"]', 'input[type="email"]', 'input[type="text"]'] },
      pass: { selectors: ['input[name="Password"]', 'input[name*="Pwd"]', 'input[name*="Pass"]', 'input[id*="pwd"]', 'input[id*="pass"]', 'input[type="password"]'] },
      repass: { selectors: ['input[name="ConfirmPassword"]', 'input[name*="ConfirmPwd"]', 'input[name*="RePwd"]', 'input[name*="RePass"]', 'input[name*="Again"]', 'input[id*="confirm"]'] }
    }
  };

  function tt88Selectors() {
       return {
      user: { selectors: ['input[name*=User]', 'input[id*=User]', 'input[type=email]', 'input[type=text]'] },
      pass: { selectors: ['input[name*=Pass]', 'input[type=password]'] },
      repass: { selectors: ['input[name*=Confirm]', 'input[id*=Confirm]'] }
    };
  }

  // GENERIC fallback
  const GENERIC = {
         user: { selectors: ['input[type=email]', 'input[name*=user]', 'input[id*=user]', 'input[name*=account]', 'input[id*=account]', 'input[type=text]'] },
    pass: { selectors: ['input[type=password]', 'input[name*=pwd]', 'input[id*=pwd]', 'input[name*=pass]', 'input[id*=pass]'] },
    repass: { selectors: ['input[name*=confirm]', 'input[id*=confirm]', 'input[name*=re]', 'input[id*=re]', 'input[name*=again]', 'input[id*=again]'] },
    withdraw: { selectors: [
      'input[formcontrolname="moneyPassword"]',
      'input[name*="Withdraw"]', 'input[id*="Withdraw"]',
      'input[name*="Fund"]', 'input[id*="Fund"]',
      'input[name*="PayPwd"]', 'input[id*="PayPwd"]',
      'input[name*="SafeWord"]', 'input[id*="SafeWord"]'
    ]},
    fullname: { selectors: [
      'input[formcontrolname="name"]',
      'input[name="RealName"]', 'input[name="FullName"]', 'input[name="Fullname"]',
      'input[name*="HoTen"]', 'input[id*="realname"]', 'input[id*="fullname"]', 'input[id*="hoten"]', 'input[name*="Name"]'
    ]},
    bankName: { selectors: ['input[name*="bankName"]', 'input[id*="bankName"]'] },
    branch: { selectors: ['input[name*="branch"]', 'input[id*="branch"]'] },
    account: { selectors: ['input[name*="account"]', 'input[id*="account"]'] }
  };

  async function fillWithRetry(data, timeoutMs) {
        const start = Date.now();
        let filledSomething = false;
        while (Date.now() - start < timeoutMs) {
          const result = await tryFillOnce(data);
          if (result === 'filled') {
              filledSomething = true;
              return true;
          } else if (result === 'found_form') {
              filledSomething = true;
          }
          await sleep(350);
        }
        if (filledSomething) { log(">>> Finished trying to fill. Some fields might be missing."); }
        else { log("!!! Timeout waiting for fields. No form elements found."); }
        return filledSomething;
  }

  async function tryFillOnce(data) {
       const conf = SITE[host.replace(/^m\./,'')] || {};
       const use = (k) => conf[k] || GENERIC[k];

       log("   Trying to find inputs...");
       const userEl = findInput(use('user'));
       const passEl = findInput(use('pass'));
       let repassEl = findInput(use('repass'));
       if (!repassEl) {
         const pws = Array.from(document.querySelectorAll('input[type="password"]'));
         if (pws.length >= 2) repassEl = pws[1];
       }
       const withdrawEl = findInput(use('withdraw'));
       const fullnameEl = findInput(use('fullname'));

       if (!userEl && !passEl && !repassEl && !fullnameEl) {
           log("   No key registration inputs found yet.");
           return 'not_found';
       }

       log("   Found some inputs. Attempting to fill...");

       let filledAny = false;
       filledAny = fill(userEl, data.username, 'username') || filledAny;
       filledAny = fill(passEl, data.password, 'password') || filledAny;
       filledAny = fill(repassEl, data.repass || data.password, 'repass') || filledAny;
       filledAny = fill(withdrawEl, data.withdraw, 'withdraw (moneyPassword)') || filledAny;
       filledAny = fill(fullnameEl, data.fullname, 'fullname (name)') || filledAny;

       const allRequiredFoundAndFilled = userEl && passEl && repassEl && fullnameEl &&
                                        data.username && data.password && (data.repass || data.password) && data.fullname;

       if(allRequiredFoundAndFilled) {
            log("   >>> All required fields seem filled.");
            return 'filled';
       } else {
            log("   >>> Some required fields might still be loading or missing.");
            return 'found_form';
       }
  }


  // Hàm này sẽ chờ và lấy data từ storage, thử lại sau mỗi 500ms
  async function getDataWithRetry(timeout = 10000) {
        let start = Date.now();
      while (Date.now() - start < timeout) {
          log("   getDataWithRetry: Reading from storage...");
          const { lastRunPayload } = await chrome.storage.local.get('lastRunPayload');
          if (lastRunPayload && lastRunPayload.data && lastRunPayload.data.username) {
              log("   getDataWithRetry: >>> Data found!", lastRunPayload.data.username);
              return lastRunPayload.data;
          }
          log("   getDataWithRetry: No data yet, retrying in 500ms...");
          await sleep(500);
      }
      log("   getDataWithRetry: !!! Timeout waiting for data.");
      return null;
  }

  // === HÀM CHẠY CHÍNH ===
  async function mainAutofillLogic() {

      // 1. Tắt popup trước (Dùng hàm mới đã cập nhật)
      const popupClosed = await closeRegisterPagePopups();
      
      // Nếu vẫn còn popup, thử lại sau một chút
      if (!popupClosed) {
          log("No popups found initially, waiting 2 seconds and trying again...");
          await sleep(2000);
          await closeRegisterPagePopups();
      }

      log("Fetching data from storage (with retry)...");
      const data = await getDataWithRetry(); // Lấy data

      if (data) {
          log("Data found. Running auto-fill...");
          // Chạy logic tự động điền
          await fillWithRetry(data, 15000);

          log("Autofill process finished. Waiting 500ms before AntiCaptcha starts...");
          await sleep(500);

      } else {
          log("No data found in lastRunPayload. Skipping auto-fill.");
      }
  }

  // VẪN GIỮ ĐỘ TRỄ 5 GIÂY TRƯỚC KHI CHẠY
  setTimeout(mainAutofillLogic, 5000);

})();