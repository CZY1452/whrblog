/**
 * SEO 工具：根据页面数据动态更新 document.head
 */

function setMeta(attr, attrValue, content) {
  let el = document.head.querySelector(`meta[${attr}="${attrValue}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, attrValue);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

export function setSeo({ title, description, keywords, ogType, ogUrl }) {
  document.title = title || 'WhrBlog';
  if (description) {
    setMeta('name', 'description', description);
    setMeta('property', 'og:description', description);
  }
  if (keywords) {
    setMeta('name', 'keywords', keywords);
  }
  if (ogType) setMeta('property', 'og:type', ogType);
  if (ogUrl) setMeta('property', 'og:url', ogUrl);
}
