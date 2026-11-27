"""A design/app.js segédei Django-sablonokhoz: ikonok, avatar-monogram és -szín."""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# A design/app.js ICONS táblájának másolata (ha a design változik, innen is frissíteni kell).
ICONS = {
    "logo": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="m14.5 12.5-4.8 4.8a1.2 1.2 0 0 1-1.7-1.7l4.8-4.8a2.6 2.6 0 0 1 3.4-3.2l-1.6 1.6.5 1.2 1.2.5 1.6-1.6a2.6 2.6 0 0 1-3.4 3.2"/>',
    "Villanyszerelő": '<path d="M13 2 4 14h7l-1 8 9-12h-7l1-8z"/>',
    "Vízszerelő": '<path d="M12 3s-6 6.6-6 11a6 6 0 0 0 12 0c0-4.4-6-11-6-11z"/><path d="M9.5 14.5a2.5 2.5 0 0 0 2.5 2.5"/>',
    "Festő": '<rect x="3" y="3" width="14" height="6" rx="1.5"/><path d="M17 6h3v6h-8v2"/><rect x="10" y="14" width="4" height="7" rx="1"/>',
    "Asztalos": '<path d="m14 7 3-3 3 3-3 3"/><path d="M17 10 7 20l-3-3L14 7"/><path d="m3 3 5 5"/>',
    "Burkoló": '<rect x="3" y="3" width="8" height="8" rx="1"/><rect x="13" y="3" width="8" height="8" rx="1"/><rect x="3" y="13" width="8" height="8" rx="1"/><rect x="13" y="13" width="8" height="8" rx="1"/>',
    "Lakatos": '<circle cx="8" cy="15" r="4.5"/><path d="m11.2 11.8 8.8-8.8"/><path d="m16.5 6.5 2.5 2.5"/><path d="m14 9 2 2"/>',
    "all": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5a7 7 0 0 1 14 0C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "locate": '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    "check": '<path d="M12 2 4 5v6c0 5 3.5 9.5 8 11 4.5-1.5 8-6 8-11V5z"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "map": '<path d="m9 4-6 2v14l6-2 6 2 6-2V4l-6 2z"/><path d="M9 4v14M15 6v14"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "inbox": '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "tool": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.5 2.5-2.4-.6-.6-2.4z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "ok": '<path d="m5 12 5 5L20 7"/>',
}
AV_COLORS = ["#1F6F5C", "#D9622B", "#1F2A44", "#7B3FA0", "#C62828", "#1565C0", "#8A5A00"]


@register.simple_tag
def icon(name, css_class=""):
    paths = ICONS.get(str(name), ICONS["tool"])
    return format_html('<svg class="icon {}" viewBox="0 0 24 24" aria-hidden="true">{}</svg>', css_class, mark_safe(paths))


@register.simple_tag
def avatar(name, css_class=""):
    name = str(name or "?")
    initials = "".join(word[0] for word in name.split() if word)[:2]
    color = AV_COLORS[sum(map(ord, name)) % len(AV_COLORS)]
    return format_html('<span class="avatar {}" style="--av:{}" aria-hidden="true">{}</span>', css_class, color, initials)
