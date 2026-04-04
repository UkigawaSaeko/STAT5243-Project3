(function () {
  "use strict";

  // =========================
  // Storage keys
  // =========================
  /** sessionStorage：仅当前标签页有效；关闭标签后重开 → 清空，可重新分桶与填问卷；同标签刷新 → 保留。 */
  var STORAGE_GROUP = "stat5243_ab_group";
  var STORAGE_SESSION = "stat5243_session_id";
  var STORAGE_SURVEY = "stat5243_survey_submitted";

  // =========================
  // Experiment constants
  // =========================
  var EXPERIMENT_NAME = "sensitive_purchase_assistant_ab";
  var cartToastTimer = null;

  // =========================
  // Runtime state
  // =========================
  var state = {
    group: null,          // "A" | "B"
    sessionId: null,
    initialized: false,
    helpWired: false,
    gaReady: false,
    gaQueue: [],
    pageViewSent: false,
    impressionSent: false,
    /** 仅在 init 完成且延迟过后置 true，此前 GA 不带 stat5243_ab / experiment_name / variant */
    gaAbParamsReady: false
  };

  // =========================
  // Utilities
  // =========================
  function isShiny() {
    return typeof window.Shiny !== "undefined" &&
      typeof window.Shiny.setInputValue === "function";
  }

  function uuid() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      var r = (Math.random() * 16) | 0;
      var v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function randomGroup() {
    return Math.random() < 0.5 ? "A" : "B";
  }

  function safeSessionGet(key) {
    try {
      return window.sessionStorage.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function safeSessionSet(key, value) {
    try {
      window.sessionStorage.setItem(key, value);
    } catch (e) {}
  }

  function getOrSetGroup() {
    var g = safeSessionGet(STORAGE_GROUP);
    if (g !== "A" && g !== "B") {
      g = randomGroup();
      safeSessionSet(STORAGE_GROUP, g);
    }
    return g;
  }

  function getOrSetSessionId() {
    var s = safeSessionGet(STORAGE_SESSION);
    if (!s) {
      s = uuid();
      safeSessionSet(STORAGE_SESSION, s);
    }
    return s;
  }

  function surveyAlreadySubmitted() {
    return safeSessionGet(STORAGE_SURVEY) === "1";
  }

  function markSurveySubmitted() {
    safeSessionSet(STORAGE_SURVEY, "1");
  }

  /** 旧版曾用 localStorage，清掉以免与 sessionStorage 策略混淆 */
  function clearLegacyLocalStorage() {
    try {
      window.localStorage.removeItem(STORAGE_GROUP);
      window.localStorage.removeItem(STORAGE_SESSION);
      window.localStorage.removeItem(STORAGE_SURVEY);
    } catch (e) {}
  }

  function stat5243AbParam(g) {
    return g === "A" ? "ab_A" : "ab_B";
  }

  function currentVariant() {
    return state.group === "A" ? "human_advisor" : "private_ai";
  }

  function currentAssistantType() {
    return state.group === "A" ? "human_advisor" : "private_ai";
  }

  function nowTs() {
    return Date.now();
  }

  function showSurveySuccessUI() {
    var fields = document.getElementById("survey-fields");
    var ok = document.getElementById("survey-success");
    if (fields) fields.style.display = "none";
    if (ok) ok.style.display = "block";
  }

  function restoreSurveyIfSubmitted() {
    if (surveyAlreadySubmitted()) {
      showSurveySuccessUI();
    }
  }

  function showCartSuccess() {
    var el = document.getElementById("cart-success");
    if (!el) return;
    el.style.display = "block";
    if (cartToastTimer) {
      clearTimeout(cartToastTimer);
    }
    cartToastTimer = window.setTimeout(function () {
      el.style.display = "none";
      cartToastTimer = null;
    }, 3500);
  }

  // =========================
  // GA handling
  // =========================
  function hasGtag() {
    return typeof window.gtag === "function";
  }

  function flushGaQueue() {
    if (!hasGtag()) return;
    state.gaReady = true;
    while (state.gaQueue.length > 0) {
      var item = state.gaQueue.shift();
      try {
        window.gtag("event", item.name, item.params || {});
      } catch (e) {}
    }
  }

  function waitForGtagAndFlush() {
    var attempts = 0;
    var maxAttempts = 40; // ~8 seconds
    var timer = window.setInterval(function () {
      attempts += 1;
      if (hasGtag()) {
        clearInterval(timer);
        flushGaQueue();
      } else if (attempts >= maxAttempts) {
        clearInterval(timer);
      }
    }, 200);
  }

  function buildBaseGaParams(extra) {
    var params = Object.assign({}, extra || {});
    if (state.gaAbParamsReady) {
      params.stat5243_ab = stat5243AbParam(state.group);
      params.experiment_name = EXPERIMENT_NAME;
      params.variant = currentVariant();
    }
    if (state.sessionId) {
      params.session_id = state.sessionId;
    }
    return params;
  }

  /** 稳定前不把「能看出哪一臂」的字段发给 GA（避免 extra 里带 assistant_type） */
  function stripArmHintsFromExtra(extra) {
    if (state.gaAbParamsReady) {
      return extra || {};
    }
    var out = Object.assign({}, extra || {});
    delete out.assistant_type;
    return out;
  }

  function sendGaEvent(name, extra) {
    var params = buildBaseGaParams(stripArmHintsFromExtra(extra));

    if (hasGtag()) {
      try {
        window.gtag("event", name, params);
      } catch (e) {
        state.gaQueue.push({ name: name, params: params });
      }
    } else {
      state.gaQueue.push({ name: name, params: params });
    }
  }

  // =========================
  // Server logging (Shiny / Flask)
  // =========================
  function sendServerEvent(eventName, payload) {
    var body = {
      event: eventName,
      payload: Object.assign({}, payload || {}, {
        ab_group: state.group,
        session_id: state.sessionId
      }),
      client_ts: nowTs()
    };

    var jsonStr = JSON.stringify(body);

    if (isShiny()) {
      window.Shiny.setInputValue("client_event", jsonStr, { priority: "event" });
      return;
    }

    fetch("/api/event", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: jsonStr,
      keepalive: true
    }).catch(function () {});
  }

  function ensureIdentity() {
    if (state.group !== "A" && state.group !== "B") {
      state.group = getOrSetGroup();
    }
    if (!state.sessionId) {
      state.sessionId = getOrSetSessionId();
    }
  }

  function trackBoth(eventName, gaExtra, serverExtra) {
    ensureIdentity();
    sendGaEvent(eventName, gaExtra || {});
    sendServerEvent(eventName, serverExtra || {});
  }

  // =========================
  // UI rendering
  // =========================
  function applyGroupUI() {
    var btn = document.getElementById("btn-help");
    var badge = document.getElementById("ab-badge");
    var headline = document.getElementById("help-headline");
    var hint = document.getElementById("help-hint");
    var avatarWrap = document.getElementById("advisor-avatar-wrap");
    var block = document.getElementById("help-block");
    var flowA = document.getElementById("help-flow-a");
    var flowB = document.getElementById("help-flow-b");

    if (!btn) return;

    if (block) {
      block.classList.remove("help-block--ai");
      if (state.group === "B") {
        block.classList.add("help-block--ai");
      }
    }

    if (state.group === "A") {
      btn.textContent = "Chat with a skin care advisor";

      if (badge) {
        badge.textContent = "Skin care specialist";
        badge.setAttribute("data-group", "A");
      }

      if (headline) {
        headline.textContent = "Questions? We're here to help.";
      }

      if (hint) {
        hint.textContent =
          "Our specialists can help you choose the right product, review how to use it, and answer common questions before you order.";
      }

      if (avatarWrap) {
        avatarWrap.style.display = "block";
        avatarWrap.setAttribute("aria-hidden", "false");
      }
    } else {
      btn.textContent = "Ask our private AI assistant";

      if (badge) {
        badge.textContent = "AI assistant · Private chat";
        badge.setAttribute("data-group", "B");
      }

      if (headline) {
        headline.textContent = "Questions? Our AI can help.";
      }

      if (hint) {
        hint.textContent =
          "An AI assistant answers your product questions on this page. Your conversation is private: it is not shared with other shoppers, sold to third parties, or used to identify you outside this session.";
      }

      if (avatarWrap) {
        avatarWrap.style.display = "none";
        avatarWrap.setAttribute("aria-hidden", "true");
      }
    }

    if (flowA && flowB) {
      flowA.style.display = state.group === "A" ? "block" : "none";
      flowB.style.display = state.group === "B" ? "block" : "none";
    }
  }

  // =========================
  // Modal handling
  // =========================
  function openModal() {
    var m = document.getElementById("help-modal");
    if (m) {
      m.classList.add("open");
      m.setAttribute("aria-hidden", "false");
    }

    trackBoth(
      "assistant_click",
      {
        assistant_type: currentAssistantType()
      },
      {
        assistant_type: currentAssistantType()
      }
    );
  }

  function closeModal() {
    var m = document.getElementById("help-modal");
    if (m) {
      m.classList.remove("open");
      m.setAttribute("aria-hidden", "true");
    }
  }

  function wireHelpButton() {
    if (state.helpWired) return;
    state.helpWired = true;

    var btn = document.getElementById("btn-help");
    if (btn) {
      btn.addEventListener("click", openModal);
    }

    var closeBtn = document.getElementById("help-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", closeModal);
    }

    var overlay = document.getElementById("help-modal");
    if (overlay) {
      overlay.addEventListener("click", function (e) {
        if (e.target === overlay) {
          closeModal();
        }
      });
    }
  }

  // =========================
  // Initial event sending
  // =========================
  function sendInitialEventsOnce() {
    ensureIdentity();
    state.gaAbParamsReady = true;

    if (!state.pageViewSent) {
      state.pageViewSent = true;
      trackBoth(
        "page_view",
        {
          page_location: window.location.href,
          page_title: document.title || "Mighty Patch"
        },
        {
          page_location: window.location.href
        }
      );
    }

    if (!state.impressionSent) {
      state.impressionSent = true;
      trackBoth(
        "experiment_impression",
        {
          assistant_type: currentAssistantType()
        },
        {
          experiment: EXPERIMENT_NAME,
          variant: currentVariant(),
          assistant_type: currentAssistantType()
        }
      );

      // Convenience event: easy to inspect in event reports
      trackBoth(
        "stat5243_" + stat5243AbParam(state.group),
        {},
        {
          experiment: EXPERIMENT_NAME,
          variant: currentVariant()
        }
      );
    }
  }

  // =========================
  // Main init
  // =========================
  function initOnce() {
    if (state.initialized) return;
    state.initialized = true;

    clearLegacyLocalStorage();

    // 1) Determine identity FIRST
    state.group = getOrSetGroup();
    state.sessionId = getOrSetSessionId();

    // 2) Render UI
    applyGroupUI();
    wireHelpButton();
    restoreSurveyIfSubmitted();

    // 3) Wait for GA if needed
    waitForGtagAndFlush();

    // 4) Send events only after group/session are definitely ready
    // Small delay avoids timing edge cases with GA bootstrap
    window.setTimeout(function () {
      sendInitialEventsOnce();
      flushGaQueue();
    }, 300);
  }

  // =========================
  // Public actions
  // =========================
  window.ABTracker = {
    addToCart: function () {
      trackBoth(
        "add_to_cart",
        {
          currency: "USD",
          value: 21.97,
          items: [{ item_name: "Mighty Patch Original 72ct" }]
        },
        {
          value: 21.97,
          item_name: "Mighty Patch Original 72ct"
        }
      );
      showCartSuccess();
    },

    claimSample: function () {
      trackBoth("claim_sample", {}, {});
    },

    surveySubmit: function () {
      if (surveyAlreadySubmitted()) {
        showSurveySuccessUI();
        return;
      }

      var embEl = document.querySelector('input[name="survey_emb"]:checked');
      var trustEl = document.querySelector('input[name="survey_trust"]:checked');

      var emb = embEl ? embEl.value : "not_answered";
      var willingness = trustEl ? trustEl.value : "not_answered";

      trackBoth(
        "survey_submit",
        {
          embarrassment: emb,
          help_willingness: willingness
        },
        {
          embarrassment: emb,
          trust: willingness
        }
      );

      markSurveySubmitted();
      showSurveySuccessUI();
    },

    getGroup: function () {
      return state.group;
    },

    getSessionId: function () {
      return state.sessionId;
    },

    closeModal: closeModal,

    showHelpReply: function (boxId, text) {
      var el = document.getElementById(boxId);
      if (el) {
        el.textContent = text;
      }
    }
  };

  // =========================
  // Boot
  // =========================
  function boot() {
    function startInit() {
      if (!state.initialized) {
        initOnce();
      }
    }

    document.addEventListener("DOMContentLoaded", function () {
      if (typeof window.Shiny !== "undefined") {
        if (typeof window.jQuery !== "undefined") {
          window.jQuery(document).one("shiny:sessioninitialized", function () {
            startInit();
          });
          // Fallback in case event doesn't fire
          window.setTimeout(startInit, 2000);
        } else {
          window.setTimeout(startInit, 1000);
        }
      } else {
        startInit();
      }
    });
  }

  boot();
})();
