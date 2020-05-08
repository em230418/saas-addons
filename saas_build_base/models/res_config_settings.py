# Copyright 2020 Eugene Molotov <https://it-projects.info/team/em230418>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import models, SUPERUSER_ID


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    def _write_values_from_master(self, vals):
        """
        This method is redefined in dependant modules
        """
        pass

    def write_values_from_master(self, vals):
        """
        This method is executed from master.
        We need extra check, that only superuser is used
        """
        assert self.env.uid == SUPERUSER_ID
        return self._write_values_from_master(vals)

    def read_values_for_master(self):
        """
        This method is also executed from master
        """
        assert self.env.uid == SUPERUSER_ID

        vals = {}
        self._read_values_for_master(vals)
        return vals

    def _read_values_for_master(self, vals):
        """
        This method is redefined in dependant modules
        """
        pass
