#!/usr/bin/python
# coding: utf-8

#
#  Outputs an anonymized, well-formed XML document that represents all relevant "interest data" of your Facebook friends.  
#

import facebook
import fbAuth
import md5
from xml.sax.saxutils import escape		


def oneWayHash(str):
	m = md5.new()
	m.update(str)
	return m.hexdigest()

def print_xml_safe(dict, key, label,output):
	val = ""
	if(key in dict):
		val = dict[key]

	if(val == None or len(val) == 0):
		val = "N/A"

	output.write("\t\t<%s>%s</%s>\n" % (label, escape(val.encode('utf-8')), label))

def print_xml_safe_array(dict, key, subkey, label,output):
	vals = []
	if(key in dict):
		for item in dict[key]:
			vals.append(item[subkey])

	val = ",".join(vals)
	if(len(val) == 0):
		val = "N/A"

	output.write("\t\t<%s>%s</%s>\n" % (label, escape(val.encode('utf-8')), label))

if __name__ == "__main__":
	graphApi = facebook.GraphAPI(fbAuth.get_token())

	friends = graphApi.get_connections("me", "friends")
	outFile = open("friendData.xml", "w+")

	outFile.write("<?xml version=\"1.0\"?>\n")
	outFile.write("<users>\n")

	# Loop through all my friends
	for friend in friends['data']:

		# Create a one-way hash of the Facebook user ID to anonymize the data
		outFile.write("\t<user id=\"%s\">\n" % (oneWayHash(friend["id"])))

		# Retrieve the friend's user object to get information such as gender, locale, etc...
		friendProfileInfo = graphApi.get_object(friend["id"])

		print_xml_safe(friendProfileInfo, "gender", "gender", outFile)
		print_xml_safe(friendProfileInfo, "locale", "locale", outFile)
		print_xml_safe_array(friendProfileInfo, "favorite_athletes", "name", "athletes", outFile)
		print_xml_safe_array(friendProfileInfo, "favorite_teams", "name", "teams", outFile)

		# Perform a FQL query to retrieve relevant data on what interests each person...        
	        result = graphApi.fql("SELECT about_me, activities, interests, music, movies, tv, books, quotes, sports FROM user WHERE uid = %s" % (friend['id']))
		
		# Somewhat valid assumption that FB UID's are, indeed, unique, and that FB doesn't lie...
		userInterests = result[0]

		print_xml_safe(userInterests, "about_me", "about", outFile)
		print_xml_safe(userInterests, "tv", "tv", outFile)
		print_xml_safe(userInterests, "movies", "movies", outFile)
		print_xml_safe(userInterests, "music", "music", outFile)
		print_xml_safe(userInterests, "books", "books", outFile)	
		print_xml_safe(userInterests, "interests", "interests", outFile)
		print_xml_safe_array(userInterests, "sports", "name", "sports", outFile)
		outFile.write("\t</user>\n")

	outFile.write("</users>")

