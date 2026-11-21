# -*- coding: utf-8 -*-
from flectra import api, fields, models
from flectra.exceptions import UserError


class SidraCorpusImportWizard(models.TransientModel):
    """UI wizard enabling administrators to load bundled default corpus or custom RGBL dataset directories."""
    _name = 'moonwitness.sidra.import.wizard'
    _description = 'Sidra Corpus Ingestion Wizard'

    dataset_dir = fields.Char(
        string='Custom Dataset Root Directory',
        default='/tmp/corpus/datasets/quran-tanzil-uthmani',
        help='Optional path to a custom uncompressed dataset folder containing manifest.json'
    )
    tradition_code = fields.Char(
        string='Tradition Code',
        default='islam',
        help='Slug of the governing tradition (e.g. islam, christianity, buddhism)'
    )
    batch_size = fields.Integer(
        string='Batch Size',
        default=1000,
        required=True,
        help='Number of records inserted per transaction before memory cache invalidation'
    )
    result_log = fields.Text(string='Ingestion Log', readonly=True)

    def action_import_bundled(self):
        self.ensure_one()
        importer = self.env['moonwitness.sidra.importer.service']
        try:
            summary = importer.import_bundled_corpus(batch_size=self.batch_size)
            self.result_log = (
                f"SUCCESS: Bundled RGBL corpus loaded — "
                f"{summary['datasets_loaded']} datasets, {summary['records_total']} records processed "
                f"({len(summary['errors'])} errors)."
            )
        except Exception as e:
            self.result_log = f"ERROR: Bundled ingestion failed: {str(e)}"
            raise UserError(f"Bundled Corpus Ingestion Error: {str(e)}")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'moonwitness.sidra.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import(self):
        self.ensure_one()
        if not self.dataset_dir:
            raise UserError("Provide a Dataset Root Directory or click 'Load All Bundled Default Datasets'.")
        importer = self.env['moonwitness.sidra.importer.service']
        try:
            count = importer.import_dataset_from_dir(
                self.dataset_dir,
                tradition_code=self.tradition_code,
                batch_size=self.batch_size
            )
            self.result_log = f"SUCCESS: Ingested {count} records from {self.dataset_dir}."
        except Exception as e:
            self.result_log = f"ERROR: Ingestion failed: {str(e)}"
            raise UserError(f"Corpus Ingestion Error: {str(e)}")

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'moonwitness.sidra.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
