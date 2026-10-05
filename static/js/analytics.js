/*
 * Suwasthik Tiles — privacy-friendly analytics events.
 *
 * Elements declare events in HTML:
 *   data-event="add_to_cart"            sent when the element is clicked
 *   data-event-on-load="product_view"   sent when the page loads
 *   data-event-params='{"item_id": "5"}' optional JSON parameters
 * Scripts can call window.stTrack(name, params).
 *
 * Nothing is sent unless an analytics provider (GA4 or Plausible) is loaded,
 * which only happens when ANALYTICS_PROVIDER and ANALYTICS_ID are set on the
 * server. Never put personal data (names, phones, emails, addresses) in params.
 */
(function () {
  function send(name, params) {
    params = params || {};
    try {
      if (typeof window.gtag === 'function') {
        window.gtag('event', name, params);
      } else if (typeof window.plausible === 'function') {
        window.plausible(name, { props: params });
      }
    } catch (e) {
      /* analytics must never break the page */
    }
  }

  function paramsOf(el) {
    var raw = el.getAttribute('data-event-params');
    if (!raw) return {};
    try { return JSON.parse(raw); } catch (e) { return {}; }
  }

  window.stTrack = send;

  document.addEventListener('click', function (event) {
    var el = event.target && event.target.closest ? event.target.closest('[data-event]') : null;
    if (el) send(el.getAttribute('data-event'), paramsOf(el));
  });

  var onLoad = document.querySelectorAll('[data-event-on-load]');
  for (var i = 0; i < onLoad.length; i++) {
    send(onLoad[i].getAttribute('data-event-on-load'), paramsOf(onLoad[i]));
  }
})();
