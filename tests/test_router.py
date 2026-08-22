from angel.router import Router
def test_combined(): assert [x[0] for x in Router().plan("what date time and weather is it","Indianapolis, IN")]==["current_datetime","current_weather"]
def test_weather(): assert Router().plan("weather","Indianapolis, IN")[0][0]=="current_weather"
def test_time(): assert Router().plan("what time is it","Indianapolis, IN")[0][0]=="current_datetime"
def test_chat(): assert Router().plan("tell me a joke","Indianapolis, IN")==[]
