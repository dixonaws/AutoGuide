"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import requests
from botocore.errorfactory import ClientError
import boto3
import json
import time
import sys
from datetime import date
from datetime import time
from datetime import datetime

def sortFunc(e):
	return e['timestamp']['S']


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
	return {
		'outputSpeech': {
			'type': 'SSML',
			'ssml': output
		},
		'card': {
			'type': 'Simple',
			'title': "SessionSpeechlet - " + title,
			'content': "SessionSpeechlet - " + output
		},
		'reprompt': {
			'outputSpeech': {
				'type': 'SSML',
				'ssml': reprompt_text
			}
		},
		'shouldEndSession': should_end_session
	}


def build_response(session_attributes, speechlet_response):
	return {
		'version': '1.0',
		'sessionAttributes': session_attributes,
		'response': speechlet_response
	}


def friendly_date(str_a_date):
	# we need to remove the last three trailing characters from the timestamp in order to be compatible with Python's
	# datetime libraries
	int_date_string_length = len(str_a_date)

	str_a_date = str_a_date[0:int_date_string_length - 3]
	print("friendly_date(): cleaned date string: " + str_a_date)

	# convert a timestamp into a Python datetime object
	date_a_date = datetime.strptime(str_a_date, "%Y-%m-%d %H:%M:%S.%f")

	str_day = str(date_a_date.day)
	str_year = str(date_a_date.year)
	str_friendly_date = date_a_date.strftime("%A") + ", " + date_a_date.strftime("%B") + " " + str_day + " " + str_year

	return (str_friendly_date)

# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
	""" If we wanted to initialize the session to have some attributes we could
	add those here
	"""

	session_attributes = {}
	card_title = "Welcome"

	strApp_id = 'cF1SE2QqJkuUgBEQHEma'
	strApp_code = 'rKLZInnnnJDvNE5ioQIMEg'

	# If the user either does not reply to the welcome message or says something
	# that is not understood, they will be prompted again with this text.
	reprompt_text = "<speak>You can ask me about your connected car, even while the ignition is off.</speak>"

	should_end_session = False

	listTrips = get_recent_trips()
	intNumberOfTrips = len(listTrips)

	speech_output = "<speak>Welcome to CarGuru. I found a total of " + str(
		intNumberOfTrips) + " trips in your profile. The three most recent were: "

	intTripNumber = 1
	for trip in listTrips:
		floatTripDistance = float(trip['odometer']['N'])
		strTripDistance = str(round(floatTripDistance, 1))
		print("float_trip_distance: " + str(floatTripDistance))
		print("str_trip_distance: " + strTripDistance)

		strTripId = str(trip['trip_id']['S'])
		strTimestamp = str(trip['timestamp']['S'])
		strLongitude = str(trip['longitude']['N'])
		strLatitude = str(trip['latitude']['N'])
		strProx = strLatitude + "," + strLongitude
		floatFuelConsumed = trip['fuel_consumed_since_restart']['N']

		# call a method to do reverse geocoding on given lat/long
		jsonLocationInfo = getLocationInfo(strProx, strApp_id, strApp_code)

		strAddressLabel = ""
		strCity = ""
		strState = ""
		strDistrict = ""

		speech_output += "Trip number " + str(intTripNumber)
		speech_output += "<break time='500ms'/>"
		speech_output += " a " + strTripDistance + " mile trip near " + jsonLocationInfo['District']
		speech_output += " on " + friendly_date(strTimestamp) + "\n"
		speech_output += "<break time='1s'/>"

		intTripNumber = intTripNumber + 1

	# // for(trip in listTrips)

	speech_output += "Which trip would you like to talk about?"
	speech_output += "</speak>"
	print(speech_output)

	return build_response(session_attributes, build_speechlet_response(
		card_title, speech_output, reprompt_text, should_end_session))


# -------------------- get_welcome_response()

def getLocationInfo(strProx, strApp_id, strApp_code):
	# this method takes the following parameters:
	# strProx = '41.8842,-87.6388,250'
	# strApp_id = 'cF1SE2QqJkuUgBEQHEma'
	# strApp_code = 'rKLZInnnnJDvNE5ioQIMEg'

	strUrl = 'https://reverse.geocoder.api.here.com/6.2/reversegeocode.json'
	dictHeaders = {'Content-Type': '*'}
	dictPayload = {
		'prox': strProx,
		'mode': 'retrieveAddresses',
		'maxresults': '1',
		'gen': '9',
		'app_id': strApp_id,
		'app_code': strApp_code
	}

	location_response = requests.get(strUrl, headers=dictHeaders, params=dictPayload)

	if (location_response.status_code == 401):
		print("Problem getting location for trip (probably an issue with your HERE credentials")
		exit(1)

	jsonResponse = location_response.json()

	return (jsonResponse['Response']['View'][0]['Result'][0]['Location']['Address'])


# -------------------- getLocationInfo()


def get_recent_trips():
	strVehicleTripTable = 'cvra-demo-VehicleTripTable-U0C6DSG0JW11'
	strRegion = 'us-east-1'

	# reverse geocoding with HERE maps
	# https://developer.here.com/documentation/geocoder/topics/example-reverse-geocoding.html
	strApp_code = 'rKLZInnnnJDvNE5ioQIMEg'
	strApp_id = 'cF1SE2QqJkuUgBEQHEma'

	dynamoDbClient = boto3.client('dynamodb', region_name=strRegion)

	sys.stdout.write('Scanning trip table ' + strVehicleTripTable + '... ')

	# intStartTime = int(time.time())

	response = []
	try:
		response = dynamoDbClient.scan(
			TableName=strVehicleTripTable,
			Select='ALL_ATTRIBUTES'
		)
	except ClientError as e:
		print()
		print("Error scanning VehicleTripTable: '" + strVehicleTripTable + "'")
		exit(1)

	# intEndTime = int(time.time())
	# intTotalTime = intEndTime - intStartTime
	#
	# print('done (' + str(intTotalTime) + 'ms).')

	listTrips = response['Items']

	# sort the list by timestamp
	# listTrips.sort(key=sortFunc)

	intRecordCount = json.dumps(response['Count'])
	print("Found " + str(intRecordCount) + " items in the trip table.")
	print("listItems is a " + str(type(listTrips)))

	# 	intTripNumber = 1
	# 	for trip in listTrips:
	# 		strVin = str(trip['vin']['S'])
	# 		strTripId = str(trip['trip_id']['S'])
	# 		strTimestamp = str(trip['timestamp']['S'])
	# 		strLongitude = str(trip['longitude']['N'])
	# 		strLatitude = str(trip['latitude']['N'])
	# 		strProx = strLatitude + "," + strLongitude
	# 		floatDistance = trip['odometer']['N']
	# 		floatFuelConsumed = trip['fuel_consumed_since_restart']['N']

	# 		# call a method to do reverse geocoding on given lat/long
	# 		jsonLocationInfo = getLocationInfo(strProx, strApp_id, strApp_code)

	# 		strAddressLabel = ""
	# 		strCity = ""
	# 		strState = ""
	# 		strDistrict = ""

	# 		try:
	# 			strAddressLabel = jsonLocationInfo['Label']
	# 			strCity = jsonLocationInfo['City']
	# 			strState = jsonLocationInfo['State']
	# 			strDistrict = jsonLocationInfo['District']
	# 		except KeyError:
	# 			pass

	# 		print("**** Trip " + str(intTripNumber) + " (trip_id: " + strTripId + ", VIN: " + strVin + ")")
	# 		print("Time: " + strTimestamp + ")")
	# 		print("Location: near " + strAddressLabel)
	# 		print("Neighborhood: " + strDistrict)
	# 		print("Distance: " + str(floatDistance) + " miles")
	# 		print("Fuel consumed: " + str(floatFuelConsumed) + " gallons")
	# 		print("All trip data: " + str(trip))
	# 		print()
	# 		intTripNumber = intTripNumber + 1
	return listTrips


# -------------------- get_recent_trips()

def handle_session_end_request():
	card_title = "Session Ended"
	speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
					"Have a nice day! "
	# Setting this to true ends the session and exits the skill.
	should_end_session = True
	return build_response({}, build_speechlet_response(
		card_title, speech_output, None, should_end_session))


def create_favorite_color_attributes(favorite_color):
	return {"favoriteColor": favorite_color}


def set_color_in_session(intent, session):
	""" Sets the color in the session and prepares the speech to reply to the
	user.
	"""

	card_title = intent['name']
	session_attributes = {}
	should_end_session = False

	if 'Color' in intent['slots']:
		favorite_color = intent['slots']['Color']['value']
		session_attributes = create_favorite_color_attributes(favorite_color)
		speech_output = "I now know your favorite color is " + \
						favorite_color + \
						". You can ask me your favorite color by saying, " \
						"what's my favorite color?"
		reprompt_text = "You can ask me your favorite color by saying, " \
						"what's my favorite color?"
	else:
		speech_output = "I'm not sure what your favorite color is. " \
						"Please try again."
		reprompt_text = "I'm not sure what your favorite color is. " \
						"You can tell me your favorite color by saying, " \
						"my favorite color is red."
	return build_response(session_attributes, build_speechlet_response(
		card_title, speech_output, reprompt_text, should_end_session))


def get_color_from_session(intent, session):
	session_attributes = {}
	reprompt_text = None

	if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
		favorite_color = session['attributes']['favoriteColor']
		speech_output = "Your favorite color is " + favorite_color + \
						". Goodbye."
		should_end_session = True
	else:
		speech_output = "I'm not sure what your favorite color is. " \
						"You can say, my favorite color is red."
		should_end_session = False

	# Setting reprompt_text to None signifies that we do not want to reprompt
	# the user. If the user does not respond or says something that is not
	# understood, the session will end.
	return build_response(session_attributes, build_speechlet_response(
		intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
	""" Called when the session starts """

	print("on_session_started requestId=" + session_started_request['requestId']
		  + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
	""" Called when the user launches the skill without specifying what they
	want
	"""

	print("on_launch requestId=" + launch_request['requestId'] +
		  ", sessionId=" + session['sessionId'])
	# Dispatch to your skill's launch
	return get_welcome_response()


def on_intent(intent_request, session):
	""" Called when the user specifies an intent for this skill """

	print("on_intent requestId=" + intent_request['requestId'] +
		  ", sessionId=" + session['sessionId'])

	intent = intent_request['intent']
	intent_name = intent_request['intent']['name']

	# Dispatch to your skill's intent handlers
	if intent_name == "MyColorIsIntent":
		return set_color_in_session(intent, session)
	elif intent_name == "WhatsMyColorIntent":
		return get_color_from_session(intent, session)
	elif intent_name == "AMAZON.HelpIntent":
		return get_welcome_response()
	elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
		return handle_session_end_request()
	else:
		raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
	""" Called when the user ends the session.

	Is not called when the skill returns should_end_session=true
	"""
	print("on_session_ended requestId=" + session_ended_request['requestId'] +
		  ", sessionId=" + session['sessionId'])


# add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
	""" Route the incoming request based on type (LaunchRequest, IntentRequest,
	etc.) The JSON body of the request is provided in the event parameter.
	"""
	print("event.session.application.applicationId=" +
		  event['session']['application']['applicationId'])

	"""
	Uncomment this if statement and populate with your skill's application ID to
	prevent someone else from configuring a skill that sends requests to this
	function.
	"""
	# if (event['session']['application']['applicationId'] !=
	#         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
	#     raise ValueError("Invalid Application ID")

	if event['session']['new']:
		on_session_started({'requestId': event['request']['requestId']},
						   event['session'])

	if event['request']['type'] == "LaunchRequest":
		return on_launch(event['request'], event['session'])
	elif event['request']['type'] == "IntentRequest":
		return on_intent(event['request'], event['session'])
	elif event['request']['type'] == "SessionEndedRequest":
		return on_session_ended(event['request'], event['session'])
