#! /usr/bin/python
# -*- coding: utf-8 -*-

## Copyright (C) 2014 Bitergia
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
## Package to deal with SCM data from *Grimoire (CVSAnalY databases)
##
## Authors:
##   Jesus M. Gonzalez-Barahona <jgb@bitergia.com>
##

from scm_query import buildSession, SCMQuery

class SCM:
    """High level interface to variables from the SCM (CVSAnalY database).

    The variable to be managed is specified when instantiating.
    The class provides functions to return different kinds of aggeregation
    (timeseries, total, list) and selection (dates, etc.)
    """

    def timeseries (self):
        """Return a timeseries for the specified variable"""

        return self.query.group_by_period().timeseries()

    def total (self):
        """Return the total count for the specified variable"""

        return self.query.scalar()

    def list (self, limit = 10):
        """Return a list for the specified variable"""

        return self.query.limit(limit).all()

    def __init__ (self, database, var, period = None, echo = False):
        """Instantiation of the object.

        - var (string): variable ("commits", "listcommits")
        - period (PeriodCondition): period condition
        - echo: write SQL queries to output stream
        """

        self.session = buildSession(
            database=database,
            echo=echo)
        if var == "ncommits":
            self.query = self.session.query().select_nscmlog(["commits",])
        elif var == "listcommits":
            self.query = self.session.query().select_listcommits()
        elif var == "nauthors":
            self.query = self.session.query().select_nscmlog(["authors",])
        elif var == "listauthors":
            self.query = self.session.query().select_listauthors()
        if period is not None:
            self.query = period.filter(self.query)


class Condition ():
    """Root of all conditions

    Provides a filter method which will be called when applying the condition.
    """

    def filter (query):
        """Filter to apply for this condition

        - query: query to which the filter will be applied
        """

        return query


class PeriodCondition (Condition):
    """Period Condition for qualifying a variable

    Specifies the period when the variable has to be considered"""

    def filter (self, query):
        """Filter to apply for this condition

        - query: query to which the filter will be applied
        """

        return query.filter_period(start = self.start,
                                   end = self.end)

    def __init__ (self, start = None, end = None):
        """Instatiation of the object.

        - start (datetime): start of the period
        - end (datetime): end of the period
        """

        self.start = start
        self.end = end
        

if __name__ == "__main__":

    from datetime import datetime

    data = SCM (database = 'mysql://jgb:XXX@localhost/vizgrimoire_cvsanaly',
                var = "ncommits")
    print data.timeseries()
    print data.total()

    period = PeriodCondition (start = datetime(2013,1,1), end = None)

    data = SCM (database = 'mysql://jgb:XXX@localhost/vizgrimoire_cvsanaly',
                var = "ncommits", period = period)
    print data.timeseries()
    print data.total()

    data = SCM (database = 'mysql://jgb:XXX@localhost/vizgrimoire_cvsanaly',
                var = "listcommits")
    print data.list()

    data = SCM (database = 'mysql://jgb:XXX@localhost/vizgrimoire_cvsanaly',
                var = "nauthors", period = period)
    print data.timeseries()
    print data.total()
