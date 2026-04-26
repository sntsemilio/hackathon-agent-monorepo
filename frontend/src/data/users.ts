import { User } from '../types';

export const USERS: User[] = [
  {
    id: 'USR-00001',
    name: 'Carla',
    segment: 'joven_digital_hey_pro',
    color: '#00C389', // verde Hey saturado
    questions: ['¿Cuánto me falta para ser Hey Pro?', 'Quiero invertir mis ahorros', '¿Qué promociones hay hoy?']
  },
  {
    id: 'USR-00010',
    name: 'Don Roberto',
    segment: 'empresario_alto_volumen',
    color: '#4A90D9', // azul corporate
    questions: ['Resumen de mis terminales', 'Límites de transferencias', 'Necesito un crédito Pyme']
  },
  {
    id: 'USR-00020',
    name: 'Ana',
    segment: 'usuario_estres_financiero',
    color: '#E8A87C', // neutro cálido
    questions: ['¿Cuándo corta mi tarjeta?', 'Opciones para pagar a meses', '¿Puedo posponer un pago?']
  },
  {
    id: 'USR-00030',
    name: 'Miguel',
    segment: 'actividad_atipica_alerta',
    color: '#FF8C42', // naranja suave
    questions: ['No reconozco un cargo', 'Bloquear mi tarjeta', 'Alerta de movimiento en madrugada']
  },
  {
    id: 'USR-00040',
    name: 'Luis',
    segment: 'profesional_prospero_inversor',
    color: '#D4AF37', // dorado sutil
    questions: ['Rendimiento de mis pagarés', '¿Cómo funcionan los fondos?', 'Diversificar portafolio']
  },
  {
    id: 'USR-00050',
    name: 'Pedro',
    segment: 'usuario_basico_bajo_enganche',
    color: '#7BC67E', // verde suave
    questions: ['¿Cómo abro una cuenta de ahorro?', 'Comisiones de cuenta básica', 'Depositar efectivo']
  },
  {
    id: 'USR-00060',
    name: 'María',
    segment: 'cliente_promedio_estable',
    color: '#8E8E93', // gris elegante
    questions: ['Pagar servicios', 'Transferencia SPEI', 'Solicitar tarjeta física']
  },
  {
    id: 'USR-00070',
    name: 'Sofía',
    segment: 'consumidor_digital_ocio',
    color: '#9b59b6', // purple 
    questions: ['Cashback en restaurantes', 'Promos en conciertos', 'Suscripciones domiciliadas']
  }
];
