# -*- coding: utf-8 -*-
import logging
from flectra.tools import config

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Automatically loads bundled default RGBL corpus datasets when moonwitness_sidra is installed."""
    if config['test_enable'] or env.registry.in_test_mode():
        _logger.info("Skipping bundled corpus auto-load in test mode.")
        return
    _logger.info("Running MoonWitness Sidra post_init_hook: loading bundled default RGBL corpus...")
    env['moonwitness.sidra.importer.service'].import_bundled_corpus(batch_size=1000)
