#!/usr/bin/python

# -*- coding: utf-8 -*-
################################################################################
# Copyright (c) 2019 University of Utah Student Computing Labs.
# All Rights Reserved.
#
# Author: Thackery Archuletta
# Creation Date: Oct 2018
# Last Updated: Feb 2019
#
# Permission to use, copy, modify, and distribute this software and
# its documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appears in all copies and
# that both that copyright notice and this permission notice appear
# in supporting documentation, and that the name of The University
# of Utah not be used in advertising or publicity pertaining to
# distribution of the software without specific, written prior
# permission. This software is supplied as is without expressed or
# implied warranties of any kind.
################################################################################

import os
import subprocess
from management_tools import loggers
import urllib2
import base64
import json
import re
import inspect
import xml.etree.cElementTree as ET
import sys


class JssServer(object):
    """Gets, posts, and deletes data from the JSS server.
    """

    def __init__(self, **kwargs):
        """Initializes JSS server.

        Args:
            **kwargs: See Keyword Args section.

        Keyword Args:
            _username (str): JSS username.
            _password (str): JSS password.
            _jss_url (str): JSS url.
            _invite (str): JSS invite for enrolling.
            _jamf_binary_1: Location of JAMF binary on computer.
            _jamf_binary_2: Location of JAMF binary on external drive.

        """
        self._username = kwargs.get('username', None)
        self._password = kwargs.get('password', None)
        self._jss_url = kwargs.get('jss_url', None)
        self._invite = kwargs.get('invite', None)
        self._jamf_binary_1 = kwargs.get('jamf_binary_1', None)
        self._jamf_binary_2 = kwargs.get('jamf_binary_2', None)

        if self._username is None:
            raise SystemExit("Username for the JSS server was not specified.")
        if self._password is None:
            raise SystemExit("Password for the JSS server was not specified.")
        if self._jss_url is None:
            raise SystemExit("JSS url for the JSS server was not specified.")

    def match(self, search_param):
        """Returns the JSS ID of a computer matching the search parameter. Fulfills JAMF's match API.

        Examples:
            This is an example of the API call made when search_param = "123456"

                https://casper.indentifier.domain:1111/JSSResource/computers/match/123456

        Args:
            search_param (str): barcode 1, barcode 2, asset tag, or serial number of computer.

        Returns:
            JSS ID (str)
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("match: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Set API request URL
        request_url = "{0}/JSSResource/computers/match/{1}".format(self._jss_url, search_param)
        logger.debug("Request URL: {}".format(request_url))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create GET request
        request = self.create_get_request_handler(request_url)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Open/send the request
        response = self.open_request_handler(request)
        logger.info("Status code from request: {}".format(response.code))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Read the JSON from the response.
        response_json = json.loads(response.read())
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get the computer data from the JSS
        try:
            computer_data = response_json['computers'][0]
        except IndexError as e:
            # If search param length is greater than 10, it is the serial number
            if len(search_param) > 10:
                logger.info("Serial number was not found in the JSS. {}".format(search_param))
            # Otherwise it's the barcode or asset tag
            else:
                logger.info("Barcode or asset not found in the JSS. {}".format(search_param))
            return None
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get JSS ID from computer data
        jss_id = str(computer_data['id'])
        logger.info("JSS ID: {}".format(jss_id))
        logger.debug("match: finished")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return jss_id

    def get_hardware_data(self, jss_id):
        """Get hardware data for computer corresponding to the JSS ID from the JSS.

        Args:
            jss_id (str): JSS ID of the computer.

        Returns:
            hardware data
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_hardware_data: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Set API request URL
        request_url = "{0}/JSSResource/computers/id/{1}/subset/Hardware".format(self._jss_url, jss_id)
        logger.debug("Request URL: {}".format(request_url))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create GET request
        request = self.create_get_request_handler(request_url)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Open/send the request
        response = self.open_request_handler(request)
        logger.info("Status code from request: {}".format(response.code))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Read the JSON from the response.
        response_json = json.loads(response.read())
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get the hardware data from the JSON
        hardware_inventory = response_json['computer']['hardware']
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_hardware_data: finished")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return hardware_inventory

    def get_general_data(self, jss_id):
        """Gets general data for computer corresponding to JSS ID from the JSS.

        Args:
            jss_id (str): JSS ID of computer

        Returns:
            General data.
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_general_data: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create API request URL
        request_url = "{0}/JSSResource/computers/id/{1}/subset/General".format(self._jss_url, jss_id)
        logger.debug("Request URL: {}".format(request_url))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create GET request
        request = self.create_get_request_handler(request_url)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Open/send the request
        response = self.open_request_handler(request)
        logger.info("Status code from request: {}".format(response.code))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Read the JSON from the response.
        response_json = json.loads(response.read())
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get the general data from the JSON
        general_inv = response_json['computer']['general']
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_general_data: finished")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return general_inv

    def get_extension_attributes(self, jss_id):
        """Gets extension attributes for computer corresponding to JSS ID from the JSS.

        Args:
            jss_id (str): JSS ID of computer

        Returns:
            Extension attributes.
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_extension_attributes: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create API request URL
        request_url = "{0}/JSSResource/computers/id/{1}/subset/extension_attributes".format(self._jss_url, jss_id)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create GET request
        request = self.create_get_request_handler(request_url)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Open/send the request
        response = self.open_request_handler(request)
        logger.info("Status code from request: {}".format(response.code))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Read the JSON from the response.
        response_json = json.loads(response.read())
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get the extension attributes from the JSON response.
        ext_attrs = response_json.get('computer', {}).get('extension_attributes', {})
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_extension_attributes: finished")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return ext_attrs

    def get_location_data(self, jss_id):
        """Gets location data for computer corresponding to JSS ID from the JSS.

        Args:
            jss_id (str): JSS ID of computer

        Returns:
            Location data.
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_location_data: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create API request URL
        request_url = "{0}/JSSResource/computers/id/{1}/subset/Location".format(self._jss_url, jss_id)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create GET request
        request = self.create_get_request_handler(request_url)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Open/send the request
        response = self.open_request_handler(request)
        logger.info("Status code from request: {}".format(response.code))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Read the JSON from the response.
        response_json = json.loads(response.read())
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get the location data from the JSON response.
        jss_location_fields = response_json.get('computer', {}).get('location', {})
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_location_data: finished")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return jss_location_fields

    def get_subsets_data(self, jss_id, xml_file):
        """Gets all the data in each subset of the xml file for the given JSS ID.

        Args:
            jss_id (str): JSS ID of computer.
            xml_file (str): File path to XML file.

        Returns:

        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_subsets_data: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Parse the xml file into an element tree
        tree = ET.parse(xml_file)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get the root element of the tree.
        root = tree.getroot()
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # For each subset in the xml file/element tree, add it to the subsets list.
        subsets = []
        for subset in root.findall("./"):
            subsets.append(subset.tag)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Initialize subset request that will be appended to the API request.
        subset_request = ""
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # For each subset in the list, add it to the subset request.
        for subset in subsets:
            subset_request += subset + "&"
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Remove the last ampersand.
        subset_request = subset_request[:-1]
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create request URL.
        request_url = "{0}/JSSResource/computers/id/{1}/subset/{2}".format(self._jss_url, jss_id, subset_request)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create GET request
        request = self.create_get_request_handler(request_url)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Open/send the request
        response = self.open_request_handler(request)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Turn the xml response into an element tree.
        xml = ET.fromstring(response.read())
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Change the element tree into an xml string.
        xml_string = ET.tostring(xml, encoding='utf-8')
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_subsets_data: finished")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return xml_string

    # TODO Remove for public version. MacGroup only.
    def get_prev_name(self, jss_id):
        """Gets previous name of computer corresponding to JSS ID.

        Notes:
            Previous name is an extension attribute.

        Args:
            jss_id (str): JSS ID of computer.

        Returns:
            Previous name of the computer (str).
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_prev_name: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get extension attributes
        ext_attrs = self.get_extension_attributes(jss_id)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Search for the previous computer name extension attribute and return it.
        for attribute in ext_attrs:
            if attribute['name'] == 'Previous Computer Names':
                prev_name = attribute['value']
                return prev_name
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_prev_name: finished")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return ""

    def delete_record(self, jss_id):
        """Delete the JSS record corresponding to the JSS ID.

        Args:
            jss_id (str): JSS ID of computer.

        Returns:
            void
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("delete_record: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Delete the JSS record.
        self._delete_handler(jss_id)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("delete_record: finished")

    def push_identity_fields(self, computer):
        """Pushes barcode, asset tag, serial number, and name fields to the JSS server.

        Args:
            computer (Computer): Provides data to send to the JSS.

        Returns:
            void
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("push_identity_fields: started")
        encoding = 'utf-8'
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # v BEGIN: Create XML structure that will be sent through the api call
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Computer: Top XML tag
        top = ET.Element('computer')
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # General tag
        general = ET.SubElement(top, 'general')
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # barcode_1 tag
        if computer.barcode_1 is not None:
            barcode_1_xml = ET.SubElement(general, 'barcode_1')
            barcode_1_xml.text = computer.barcode_1.decode(encoding)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # barcode_2 tag
        if computer.barcode_2 is not None:
            barcode_2_xml = ET.SubElement(general, 'barcode_2')
            barcode_2_xml.text = computer.barcode_2.decode(encoding)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # asset_tag tag
        if computer.asset_tag is not None:
            asset_tag_xml = ET.SubElement(general, 'asset_tag')
            asset_tag_xml.text = computer.asset_tag.decode(encoding)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        if computer.serial_number is not None:
            serial_number_xml = ET.SubElement(general, 'serial_number')
            serial_number_xml.text = computer.serial_number.decode(encoding)

        if computer.name is not None:
            name_xml = ET.SubElement(general, 'name')
            name_xml.text = computer.name.decode(encoding)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # ^ END: Create XML structure that will be sent through the api call
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Convert xml tree to an xml string.
        xml = ET.tostring(top)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Push xml string and update the computer in the JSS.
        self._push_xml_handler(xml, computer.jss_id)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("push_identity_fields: finished")

    def push_xml(self, xml, jss_id):
        """Push data from XML file to update JSS record for the given JSS ID.

        Args:
            xml (str): File path of XML file.
            jss_id (str): JSS ID of computer.

        Returns:
            void
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("push_xml: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Parse XML file into an element tree.
        tree = ET.parse(xml)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Convert element tree into an XML string.
        xml = ET.tostring(tree.getroot(), encoding='utf-8')
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Remove new lines from xml string.
        xml = re.sub("\n", "", xml)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Remove white space between tags.
        xml = re.sub("(>)\s+(<)", r"\1\2", xml)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Push XML string to udpate JSS record.
        self._push_xml_handler(xml, jss_id)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("push_xml: finished")

    def push_xml_str(self, xml_str, jss_id):
        """Push data from XML string to update JSS record for the given JSS ID.

        Args:
            xml (str): XML string
            jss_id (str): JSS ID of computer.

        Returns:
            void
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("push_xml_str: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Remove new lines from xml string.
        xml_str = re.sub("\n", "", xml_str)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Remove white space between tags.
        xml_str = re.sub("(>)\s+(<)", r"\1\2", xml_str)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Push XML string to udpate JSS record.
        self._push_xml_handler(xml_str, jss_id)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("push_xml_str: finished")

    def get_serial(self, jss_id):
        """Gets the serial number for the computer corresponding to JSS ID from the JSS.

        Args:
            jss_id (str): JSS ID of computer

        Returns:
            Serial number of computer according to the JSS. (str)
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_serial: started")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get general data.
        general_data = self.get_general_data(jss_id)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get serial number.
        jss_serial = general_data['serial_number']
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("get_serial: finished")
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return jss_serial

    def get_managed_status(self, jss_id):
        """Get managed status of computer corresponding to JSS ID.

        Args:
            jss_id (str): JSS ID of computer

        Returns:
            Managed status of computer. (str)
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug('get_managed_status: started')
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get general data.
        general_data = self.get_general_data(jss_id)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get remote management data.
        remote_mangement_data = general_data['remote_management']
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Get management status
        managed = str(remote_mangement_data['managed']).lower()
        logger.debug('Management status: {}'.format(managed))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug('get_managed_status: finished')
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return managed

    def get_barcode_1(self, jss_id):
        logger.debug("get_barcode_1: started")
        general_set = self.get_general_data(jss_id)
        barcode = general_set['barcode_1']
        logger.debug("get_barcode_1: finished")
        return barcode

    def get_barcode_2(self, jss_id):
        logger.debug("get_barcode_2: started")
        general_set = self.get_general_data(jss_id)
        barcode = general_set['barcode_2']
        logger.debug("get_barcode_2: finished")
        return barcode

    def get_asset_tag(self, jss_id):
        logger.debug("get_asset_tag: started")
        general_set = self.get_general_data(jss_id)
        asset = general_set['asset_tag']
        logger.debug("get_asset_tag: finished")
        return asset

    def get_computer_name(self, jss_id):
        logger.debug("get_computer_name: started")
        general_set = self.get_general_data(jss_id)
        name = general_set['name'].encode('utf-8')
        logger.debug("get_computer_name: finished")
        return name

    def enroll_computer(self):
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        logger.debug("enroll_computer: activated")
        logger.info('Enrolling computer.')
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        cmd = [self._jamf_binary_1, 'enroll', '-invitation', self._invite, '-noPolicy', '-noManage', '-verbose']
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Enroll computer
        try:
            # enroll_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            '''
            If this process hangs when jamf is running softwareupdate, go to Settings>Computer Management>Inventory
            Collection>General and uncheck 'Include home directory sizes'. I also uncheck 'Collect available software 
            updates' for the purpose of testing.
            '''
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            while proc.poll() is None:
                line = proc.stdout.readline()
                line = line.strip()
                if line != "":
                    ERASE_LINE = '\x1b[2K'
                    sys.stdout.write('{}Enrolling: {}\r'.format(ERASE_LINE, line))
                    sys.stdout.flush()
            print("")

            logger.info('Enrolling finished.')
            logger.debug('enroll_computer: finished')
            return True
        except (OSError, subprocess.CalledProcessError) as e:
            # if e.errno == 2:
            logger.error("Couldn't find " + self._jamf_binary_2 + ". Enrolling failed. " + str(e))
            try:
                logger.info("Enrolling again. Now using " + self._jamf_binary_2)

                conf_cmd = [self._jamf_binary_2, 'createConf', '-url', self._jss_url, '-verifySSLCert', 'never']
                conf_output = subprocess.check_output(conf_cmd, stderr=subprocess.STDOUT)
                logger.debug(conf_output)
                enroll_cmd = [self._jamf_binary_2, 'enroll', '-invitation', self._invite, '-noPolicy', '-noManage', '-verbose']
                enroll_output = subprocess.check_output(enroll_cmd, stderr=subprocess.STDOUT)
                logger.debug(enroll_output)
                logger.info('Enrolling finished.')
                logger.debug('enroll_computer: finished')
                return True
            except subprocess.CalledProcessError as e:
                logger.error(e.output)
                logger.info("enroll_computer: failed")
                raise
            except Exception as e:
                logger.error("  > Either the path to " + self._jamf_binary_2 + " is incorrect or JAMF has not "
                                                                "been installed on this computer. ")
                logger.error(e)
                logger.info("enroll_computer: failed")
                raise

    def _delete_handler(self, jss_id):
        logger.debug("_delete_handler: started")
        request_url = "{}/JSSResource/computers/id/{}".format(self._jss_url, jss_id)
        logger.debug("Request URL: {}".format(request_url))
        request = urllib2.Request(request_url)
        request.add_header('Authorization', 'Basic ' + base64.b64encode(self._username + ':' + self._password))
        request.get_method = lambda: 'DELETE'

        response = self.open_request_handler(request)
        logger.debug("  HTML DELETE response code: {}".format(response.code))
        logger.debug("_delete_handler: finished")

    def open_request_handler(self, request):
        """Opens urllib2.Request.

        Args:
            request (urllib2.Request): Request to send.

        Returns:
            response from request
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Open the request and handle it accordingly.
        try:
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as error:
            contents = error.read()
            logger.error("HTTP error contents: {}".format(contents))
            if error.code == 400:
                logger.error("HTTP code {}: {}".format(error.code, "Request error."))
            elif error.code == 401:
                logger.error("HTTP code {}: {}".format(error.code, "Authorization error."))
            elif error.code == 403:
                logger.error("HTTP code {}: {}".format(error.code, "Permissions error."))
            elif error.code == 404:
                logger.error("HTTP code {}: {}".format(error.code, "Resource not found."))
            elif error.code == 409:
                error_message = re.findall("Error: (.*)<", contents)
                logger.error("HTTP code {}: {} {}".format(error.code, "Resource conflict", error_message[0]))
            else:
                logger.error("HTTP code {}: {}".format(error.code, "Misc HTTP error."))
            raise error
        except urllib2.URLError as error:
            logger.error("URL error reason: {}".format(error.reason))
            logger.error("Error contacting JSS.")
            raise error
        except Exception as error:
            logger.debug("Error submitting to JSS: {}".format(error))
            raise error
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return response

    def create_get_request_handler(self, request_url):
        """Creates a GET request from a URL.

        Args:
            request_url (str): The request URL.

        Returns:
            The created request.
        """
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Create a request
        request = urllib2.Request(request_url)
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        # Add headers to the request
        request.add_header('Accept', 'application/json')
        # Format credentials for header.
        creds = base64.b64encode("{}:{}".format(self._username, self._password))
        # Add credentials to header
        request.add_header('Authorization', 'Basic {}'.format(creds))
        # <><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
        return request

    def _push_xml_handler(self, xml, jss_id):
        logger.debug("_push_xml_handler: started")
        request_url = "{}/JSSResource/computers/id/{}".format(self._jss_url, jss_id)
        logger.debug("Request URL: {}".format(request_url))

        request = urllib2.Request(request_url, data=xml)
        request.add_header('Authorization', 'Basic ' + base64.b64encode(self._username + ':' + self._password))
        request.add_header('Content-Type', 'text/xml')
        request.get_method = lambda: 'PUT'

        response = self.open_request_handler(request)
        logger.info("   HTML PUT response code: {}".format(response.code))
        logger.debug("_push_xml_handler: finished")


cf = inspect.currentframe()
abs_file_path = inspect.getframeinfo(cf).filename
basename = os.path.basename(abs_file_path)
lbasename = os.path.splitext(basename)[0]
logger = loggers.FileLogger(name=lbasename, level=loggers.DEBUG)
logger.debug("{} logger started.".format(lbasename))


