// Populate the sidebar
//
// This is a script, and not included directly in the page, to control the total size of the book.
// The TOC contains an entry for each page, so if each page includes a copy of the TOC,
// the total size of the page becomes O(n**2).
class MDBookSidebarScrollbox extends HTMLElement {
    constructor() {
        super();
    }
    connectedCallback() {
        this.innerHTML = '<ol class="chapter"><li class="chapter-item expanded affix "><a href="index.html">Introduction</a></li><li class="chapter-item expanded "><a href="qsa-api/index.html"><strong aria-hidden="true">1.</strong> QSA REST API</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="qsa-api/installation.html"><strong aria-hidden="true">1.1.</strong> Installation</a></li><li class="chapter-item expanded "><a href="qsa-api/configuration.html"><strong aria-hidden="true">1.2.</strong> Configuration</a></li><li class="chapter-item expanded "><a href="qsa-api/endpoints/index.html"><strong aria-hidden="true">1.3.</strong> Endpoints</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="qsa-api/endpoints/symbology.html"><strong aria-hidden="true">1.3.1.</strong> /api/symbology</a></li><li class="chapter-item expanded "><a href="qsa-api/endpoints/projects.html"><strong aria-hidden="true">1.3.2.</strong> /api/projects</a></li><li class="chapter-item expanded "><a href="qsa-api/endpoints/processing.html"><strong aria-hidden="true">1.3.3.</strong> /api/processing</a></li><li class="chapter-item expanded "><a href="qsa-api/endpoints/instances.html"><strong aria-hidden="true">1.3.4.</strong> /api/instances</a></li></ol></li></ol></li><li class="chapter-item expanded "><a href="qsa-plugin/index.html"><strong aria-hidden="true">2.</strong> QSA plugin</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="qsa-plugin/installation.html"><strong aria-hidden="true">2.1.</strong> Installation</a></li><li class="chapter-item expanded "><a href="qsa-plugin/configuration.html"><strong aria-hidden="true">2.2.</strong> Configuration</a></li><li class="chapter-item expanded "><a href="qsa-plugin/usage.html"><strong aria-hidden="true">2.3.</strong> Usage</a></li></ol></li><li class="chapter-item expanded "><a href="qsa-cli/index.html"><strong aria-hidden="true">3.</strong> QSA cli</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="qsa-cli/installation.html"><strong aria-hidden="true">3.1.</strong> Installation</a></li><li class="chapter-item expanded "><a href="qsa-cli/configuration.html"><strong aria-hidden="true">3.2.</strong> Configuration</a></li><li class="chapter-item expanded "><a href="qsa-cli/commands.html"><strong aria-hidden="true">3.3.</strong> Commands</a></li></ol></li><li class="chapter-item expanded "><a href="sandbox/index.html"><strong aria-hidden="true">4.</strong> Sandbox</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="sandbox/inspect.html"><strong aria-hidden="true">4.1.</strong> Introspection</a></li><li class="chapter-item expanded "><a href="sandbox/projects.html"><strong aria-hidden="true">4.2.</strong> Projects</a></li><li class="chapter-item expanded "><a href="sandbox/vector/index.html"><strong aria-hidden="true">4.3.</strong> Vector</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="sandbox/vector/layers.html"><strong aria-hidden="true">4.3.1.</strong> Layers</a></li><li class="chapter-item expanded "><a href="sandbox/vector/styles.html"><strong aria-hidden="true">4.3.2.</strong> Styles</a></li></ol></li><li class="chapter-item expanded "><a href="sandbox/raster/index.html"><strong aria-hidden="true">4.4.</strong> Raster</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="sandbox/raster/layers.html"><strong aria-hidden="true">4.4.1.</strong> Layers</a></li><li class="chapter-item expanded "><a href="sandbox/raster/styles.html"><strong aria-hidden="true">4.4.2.</strong> Styles</a></li><li class="chapter-item expanded "><a href="sandbox/raster/processing.html"><strong aria-hidden="true">4.4.3.</strong> Processing</a></li></ol></li></ol></li><li class="chapter-item expanded "><a href="DEVELOPERS.html"><strong aria-hidden="true">5.</strong> Developers</a></li><li class="chapter-item expanded "><a href="FUNDERS.html"><strong aria-hidden="true">6.</strong> Funders</a></li></ol>';
        // Set the current, active page, and reveal it if it's hidden
        let current_page = document.location.href.toString();
        if (current_page.endsWith("/")) {
            current_page += "index.html";
        }
        var links = Array.prototype.slice.call(this.querySelectorAll("a"));
        var l = links.length;
        for (var i = 0; i < l; ++i) {
            var link = links[i];
            var href = link.getAttribute("href");
            if (href && !href.startsWith("#") && !/^(?:[a-z+]+:)?\/\//.test(href)) {
                link.href = path_to_root + href;
            }
            // The "index" page is supposed to alias the first chapter in the book.
            if (link.href === current_page || (i === 0 && path_to_root === "" && current_page.endsWith("/index.html"))) {
                link.classList.add("active");
                var parent = link.parentElement;
                if (parent && parent.classList.contains("chapter-item")) {
                    parent.classList.add("expanded");
                }
                while (parent) {
                    if (parent.tagName === "LI" && parent.previousElementSibling) {
                        if (parent.previousElementSibling.classList.contains("chapter-item")) {
                            parent.previousElementSibling.classList.add("expanded");
                        }
                    }
                    parent = parent.parentElement;
                }
            }
        }
        // Track and set sidebar scroll position
        this.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                sessionStorage.setItem('sidebar-scroll', this.scrollTop);
            }
        }, { passive: true });
        var sidebarScrollTop = sessionStorage.getItem('sidebar-scroll');
        sessionStorage.removeItem('sidebar-scroll');
        if (sidebarScrollTop) {
            // preserve sidebar scroll position when navigating via links within sidebar
            this.scrollTop = sidebarScrollTop;
        } else {
            // scroll sidebar to current active section when navigating via "next/previous chapter" buttons
            var activeSection = document.querySelector('#sidebar .active');
            if (activeSection) {
                activeSection.scrollIntoView({ block: 'center' });
            }
        }
        // Toggle buttons
        var sidebarAnchorToggles = document.querySelectorAll('#sidebar a.toggle');
        function toggleSection(ev) {
            ev.currentTarget.parentElement.classList.toggle('expanded');
        }
        Array.from(sidebarAnchorToggles).forEach(function (el) {
            el.addEventListener('click', toggleSection);
        });
    }
}
window.customElements.define("mdbook-sidebar-scrollbox", MDBookSidebarScrollbox);
