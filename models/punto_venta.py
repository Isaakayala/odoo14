# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class PuntoVenta(models.Model):
    _name = 'punto.venta'
    _description = 'Punto de Venta'

    folio_number = fields.Char(readonly=True, copy=False)
    order_number = fields.Char(string='Número de Orden', readonly=True)
    date = fields.Datetime(string='Fecha de Venta', default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    order_line_ids = fields.One2many('punto.venta.line', 'venta_id', string='Líneas de Venta')
    subtotal_amount = fields.Float(compute='_compute_subtotal_amount', string='Subtotal', store=True)  # Corrección aquí
    total_amount = fields.Float(compute='_compute_total_amount', string='Total de Venta', store=True)

    @api.model
    def create(self, vals):
        # Generar el número de folio
        vals['folio_number'] = self.env['ir.sequence'].next_by_code('punto.venta.folio') or '/'

        # Generar el número de orden de venta
        year = datetime.now().year
        month = datetime.now().month
        sequence = self.env['ir.sequence'].next_by_code('punto.venta.order') or '0001'
        
        vals['order_number'] = f'VENTA/{year}/{month:02}/{sequence.zfill(4)}'
    
        return super(PuntoVenta, self).create(vals)

    @api.depends('order_line_ids.price_total')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = sum(line.price_total for line in order.order_line_ids)

    @api.depends('order_line_ids.price_total')
    def _compute_subtotal_amount(self):
        for order in self:
            order.subtotal_amount = sum(line.price_total for line in order.order_line_ids)

    def unlink(self):
        # Lógica para reiniciar la secuencia si es necesario
        for record in self:
            if record.order_number:
                if not self.search_count([('order_number', '!=', record.order_number)]):
                    sequence = self.env['ir.sequence'].search([('code', '=', 'punto.venta.order')])
                    if sequence:
                        sequence.write({'number_next': 1})

        return super(PuntoVenta, self).unlink()

    def action_add_payment(self):
        """ Abre un formulario para registrar un pago a la venta. """
        self.ensure_one()  # Asegúrate de que solo se esté trabajando con una venta
        return {
            'name': 'Registrar Pago',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'punto.venta.payment',  # Cambia esto al nombre de tu modelo de pago
            'type': 'ir.actions.act_window',
            'context': {
                'default_venta_id': self.id,  # Asigna la venta actual al nuevo pago
            },
            'target': 'new',  # Abre en una ventana modal
        }

class PuntoVentaLine(models.Model):
    _name = 'punto.venta.line'
    _description = 'Línea de Venta'

    venta_id = fields.Many2one('punto.venta', string='Venta')
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    quantity = fields.Float(string='Cantidad', default=1, required=True)
    price_unit = fields.Float(related='product_id.list_price', string='Precio Unitario', readonly=True)
    subtotal = fields.Float(compute='_compute_subtotal', string='Subtotal', store=True)
    price_total = fields.Float(compute='_compute_price_total', string='Total', store=True)
    taxes_id = fields.Many2many('account.tax', string='Impuestos', related='product_id.taxes_id', readonly=False)

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit  # Calcula el subtotal sin impuestos


    @api.depends('quantity', 'price_unit', 'taxes_id')
    def _compute_price_total(self):
        for line in self:
            # Calcular el subtotal como la suma de los precios unitarios por la cantidad
            subtotal = line.quantity * line.price_unit
            line.subtotal = subtotal  # Asignar el subtotal al campo correspondiente

            # Inicializa total con el subtotal
            total = subtotal
        
            # Sumar los impuestos si existen
            if line.taxes_id:
                total += sum(tax.amount for tax in line.taxes_id)  # Suma los impuestos
        
            # Asignar el total al campo price_total
            line.price_total = total

class PuntoVentaPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Registro de Pagos de Ventas'

    venta_id = fields.Many2one('punto.venta', string='Venta', required=True)

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