# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PuntoVentaPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Registro de Pagos de Ventas'

    venta_id = fields.Many2one('punto.venta', string='Venta', required=True)
    payment_date = fields.Date(string="Fecha de pago")

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError("El monto del pago debe ser mayor que cero.")

    def action_post(self):
        """ Lógica para confirmar el pago. """
        super(PuntoVentaPayment, self).action_post()
        for record in self:
            if record.venta_id:
                # Aquí puedes agregar lógica para marcar la venta como pagada, si es necesario
                pass