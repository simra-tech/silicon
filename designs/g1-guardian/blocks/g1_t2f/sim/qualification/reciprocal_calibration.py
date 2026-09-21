"""Frozen physical approximation, using only a sample's25/100C calibration.
If frequency=K*T_K/(V0+a*T_K), then1/frequency=A/T_K+B.
Resistor TC, comparator delay and nonlinear reference curvature limit the model.
No ensemble fit, clipping, correction table or extra calibration measurement.
"""
KELVIN_OFFSET=273.15
def fit_calibration(frequency25,frequency100):
 if not 0<frequency25<frequency100:raise ValueError('Calibration requires positive increasing frequency')
 t1,t2=25+KELVIN_OFFSET,100+KELVIN_OFFSET
 a=(1/frequency100-1/frequency25)/(1/t2-1/t1)
 b=1/frequency25-a/t1
 return a,b
def infer_temperature(frequency,a,b):
 if frequency<=0 or 1/frequency-b<=0:raise ValueError('Nonphysical reciprocal-model denominator')
 return a/(1/frequency-b)-KELVIN_OFFSET
