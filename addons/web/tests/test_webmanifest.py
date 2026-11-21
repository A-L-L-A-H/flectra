# -*- coding: utf-8 -*-
# Part of Flectra. See LICENSE file for full copyright and licensing details.

from flectra.addons.base.tests.common import HttpCaseWithUserDemo
from flectra.tests.common import tagged


@tagged("-at_install", "post_install")
class WebManifestRoutesTest(HttpCaseWithUserDemo):
    """
    This test suite is used to request the routes used by the PWA backend implementation
    """

    def test_webmanifest(self):
        """
        This route returns a well formed backend's WebManifest
        """
        self.authenticate("admin", "admin")
        response = self.url_open("/web/manifest.webmanifest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/manifest+json")
        data = response.json()
        self.assertEqual(data["name"], "MoonWitness")
        self.assertEqual(data["scope"], "/web")
        self.assertEqual(data["start_url"], "/web")
        self.assertEqual(data["display"], "standalone")
        self.assertEqual(data["background_color"], "#0b0c0e")
        self.assertEqual(data["theme_color"], "#f28b3c")
        self.assertEqual(data["prefer_related_applications"], False)
        self.assertEqual(data["icons"], [{
            'src': '/moonwitness_base/static/src/img/moonwitness-mark.svg',
            'sizes': 'any',
            'type': 'image/svg+xml',
            'purpose': 'any',
        }])
        self.assertGreaterEqual(len(data["shortcuts"]), 0)
        for shortcut in data["shortcuts"]:
            self.assertGreater(len(shortcut["name"]), 0)
            self.assertGreater(len(shortcut["description"]), 0)
            self.assertGreater(len(shortcut["icons"]), 0)
            self.assertTrue(shortcut["url"].startswith("/web#menu_id="))


    def test_webmanifest_legacy_configured_brand_is_normalized(self):
        """Previously stored product labels must not leak into the installed app manifest."""
        self.env['ir.config_parameter'].sudo().set_param('web.web_app_name', 'Flectra 3.0')
        response = self.url_open("/web/manifest.webmanifest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "MoonWitness")

    def test_webmanifest_unauthenticated(self):
        """
        This route returns a well formed backend's WebManifest
        """
        response = self.url_open("/web/manifest.webmanifest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/manifest+json")
        data = response.json()
        self.assertEqual(data["name"], "MoonWitness")
        self.assertEqual(data["scope"], "/web")
        self.assertEqual(data["start_url"], "/web")
        self.assertEqual(data["display"], "standalone")
        self.assertEqual(data["background_color"], "#0b0c0e")
        self.assertEqual(data["theme_color"], "#f28b3c")
        self.assertEqual(data["prefer_related_applications"], False)
        self.assertEqual(data["icons"], [{
            'src': '/moonwitness_base/static/src/img/moonwitness-mark.svg',
            'sizes': 'any',
            'type': 'image/svg+xml',
            'purpose': 'any',
        }])
        self.assertEqual(len(data["shortcuts"]), 0)

    def test_serviceworker(self):
        """
        This route returns a JavaScript's ServiceWorker
        """
        response = self.url_open("/web/service-worker.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/javascript")
        self.assertEqual(response.headers["Service-Worker-Allowed"], "/web")

    def test_offline_url(self):
        """
        This route returns the offline page
        """
        response = self.url_open("/web/offline")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")

    def test_apple_touch_icon(self):
        """
        This request tests the presence of an apple-touch-icon image route for the PWA icon and
        its presence from the head of the document.
        """
        self.authenticate("demo", "demo")
        response = self.url_open("/moonwitness_base/static/description/icon.png")
        self.assertEqual(response.status_code, 200)

        document = self.url_open("/web")
        self.assertIn(
            '<link rel="apple-touch-icon" href="/moonwitness_base/static/description/icon.png"/>', document.text,
            "Icon for iOS is present in the head of the document.",
        )
