#!/usr/bin/env python

# Copyright (C) 2014 Bitergia
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
# Authors:
#     Alvaro del Castillor <acs@bitergia.com>
#

""" People and Companies evolution per quarters """

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


from vizgrimoire.analysis.analyses import Analyses
from vizgrimoire.metrics.query_builder import DSQuery
from vizgrimoire.metrics.metrics_filter import MetricFilters
from vizgrimoire.GrimoireUtils import createJSON
from vizgrimoire.SCR import SCR

class QuartersData(Analyses):
    id = "quarters_data"
    name = "Quarters Data"
    desc = "Metrics by Quarter"

    def create_report(self, data_source, destdir):
        if data_source != SCR: return None
        self.result(data_source, destdir)

    def result(self, data_source, destdir = None):
        if data_source != SCR or destdir is None: return None

        period = self.filters.period
        startdate = self.filters.startdate
        enddate = self.filters.enddate
        idb = self.db.identities_db
        bots = SCR.get_bots()

        # people = self.db.GetPeopleList("'"+startdate+"'", "'"+enddate+"'", SCR.get_bots())
        people = self.db.GetPeopleList(startdate, enddate, bots)
        createJSON(people, destdir+"/scr-people-all.json", False)
        organizations = self.db.GetCompaniesName(startdate, enddate)
        createJSON(organizations, destdir+"/scr-organizations-all.json", False)

        start = datetime.strptime(startdate.replace("'",""), "%Y-%m-%d")
        start_quarter = (start.month-1)%3 + 1
        end = datetime.strptime(enddate.replace("'",""), "%Y-%m-%d")
        end_quarter = (end.month-1)%3 + 1

        organizations_quarters = {}
        people_quarters = {}

        quarters = (end.year - start.year) * 4 + (end_quarter - start_quarter)

        for i in range(0, quarters+1):
            year = start.year
            quarter = (i%4)+1
            # logging.info("Analyzing organizations and people quarter " + str(year) + " " +  str(quarter))
            data = self.db.GetCompaniesQuarters(year, quarter)
            organizations_quarters[str(year)+" "+str(quarter)] = data
            data_people = self.db.GetPeopleQuarters(year, quarter, 25, bots)
            people_quarters[str(year)+" "+str(quarter)] = data_people
            start = start + relativedelta(months=3)
        createJSON(organizations_quarters, destdir+"/scr-organizations-quarters.json")
        createJSON(people_quarters, destdir+"/scr-people-quarters.json")

    def get_report_files(self, data_source = None):
        if data_source is not SCR: return []
        return ["scr-people-all.json",
                "scr-organizations-all.json",
                "scr-organizations-quarters.json",
                "scr-people-quarters.json"]
