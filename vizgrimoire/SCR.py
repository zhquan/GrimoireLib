## Copyright (C) 2013-2014 Bitergia
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
## This file is a part of the vizGrimoire R package
##  (an R library for the MetricsGrimoire and vizGrimoire systems)
##
##
## Queries for source code review data analysis
##
##
## Authors:
##   Daniel Izquierdo <dizquierdo@bitergia.com>
##   Alvaro del Castillo San Felix <acs@bitergia.com>

import logging, os, sys
from numpy import median, average
import time
from datetime import datetime, timedelta

from GrimoireSQL import GetSQLGlobal, GetSQLPeriod
from GrimoireSQL import ExecuteQuery
from GrimoireUtils import GetPercentageDiff, GetDates, completePeriodIds
from GrimoireUtils import checkListArray, removeDecimals, get_subprojects
from GrimoireUtils import getPeriod, createJSON, checkFloatArray, medianAndAvgByPeriod
from metrics_filter import MetricFilters


from data_source import DataSource
from filter import Filter


class SCR(DataSource):
    _metrics_set = []

    @staticmethod
    def get_db_name():
        return "db_gerrit"

    @staticmethod
    def get_name(): return "scr"

    @staticmethod
    def get_metrics_not_filters():
        metrics_not_filters =  ['verified','codereview','sent','WaitingForReviewer','WaitingForSubmitter','approved']
        return metrics_not_filters

    @staticmethod
    def get_date_init(startdate = None, enddate = None, identities_db = None, type_analysis = None):
        q = " SELECT DATE_FORMAT (MIN(submitted_on), '%Y-%m-%d') as first_date FROM issues"
        return(ExecuteQuery(q))

    @staticmethod
    def get_date_end(startdate = None, enddate = None, identities_db = None, type_analysis = None):
        q = " SELECT DATE_FORMAT (MAX(changed_on), '%Y-%m-%d') as last_date FROM changes"
        return(ExecuteQuery(q))

    @staticmethod
    def get_evolutionary_data (period, startdate, enddate, identities_db, filter_ = None):
        return SCR.__get_data__ (period, startdate, enddate, identities_db, filter_, True)

    @staticmethod
    def create_evolutionary_report (period, startdate, enddate, destdir, i_db, filter_ = None):
        data =  SCR.get_evolutionary_data (period, startdate, enddate, i_db, filter_)
        filename = SCR().get_evolutionary_filename()
        createJSON (data, os.path.join(destdir, filename))

    @staticmethod
    def get_agg_data (period, startdate, enddate, identities_db, filter_ = None):
        return SCR.__get_data__ (period, startdate, enddate, identities_db, filter_)

    @staticmethod
    def __get_data__ (period, startdate, enddate, identities_db, filter_ = None, evol = False):
        data = {}
        DS = SCR

        type_analysis = None
        if filter_ is not None:
            type_analysis = [filter_.get_name(), filter_.get_item()]

        from report import Report
        automator = Report.get_config()

        if evol:
            metrics_on = DS.get_metrics_core_ts()
            automator_metrics = DS.get_name()+"_metrics_ts"
        else:
            metrics_on = DS.get_metrics_core_agg()
            automator_metrics = DS.get_name()+"_metrics_agg"

        if automator_metrics in automator['r']:
            metrics_on = automator['r'][automator_metrics].split(",")
            logging.info(automator_metrics + " found ")
            print(metrics_on)

        metrics_reports = SCR.get_metrics_core_reports()
        if filter_ is None:
            from report import Report
            reports_on = Report.get_config()['r']['reports'].split(",")
            for r in metrics_reports:
                if r in reports_on: metrics_on += [r]

        if DS.get_name()+"_start_date" in Report.get_config()['r']:
            startdate = "'"+Report.get_config()['r'][DS.get_name()+"_start_date"]+"'"
        if DS.get_name()+"_end_date" in Report.get_config()['r']:
            enddate = "'"+Report.get_config()['r'][DS.get_name()+"_end_date"]+"'"

        mfilter = MetricFilters(period, startdate, enddate, type_analysis)
        all_metrics = SCR.get_metrics_set(SCR)

        # SCR specific: remove some metrics from filters
        if filter_ is not None:
            metrics_not_filters =  SCR.get_metrics_not_filters()
            metrics_on_filters = list(set(metrics_on) - set(metrics_not_filters))
            if filter_.get_name() == "repository": 
                if 'review_time' in metrics_on: metrics_on_filters+= ['review_time']
                if 'submitted' in metrics_on: metrics_on_filters+= ['submitted']
            metrics_on = metrics_on_filters
        # END SCR specific

        for item in all_metrics:
            if item.id not in metrics_on: continue
            item.filters = mfilter
            if not evol: mvalue = item.get_agg()
            else:        mvalue = item.get_ts()
            data = dict(data.items() + mvalue.items())


        # SCR SPECIFIC #
        if evol:
            metrics_on_changes = ['merged','abandoned','new']
            for item in all_metrics:
                if item.id in metrics_on_changes and filter_ is None:
                    mvalue = item.get_ts_changes()
                    data = dict(data.items() + mvalue.items())
        # END SCR SPECIFIC #

        if not evol:
            init_date = DS.get_date_init(startdate, enddate, identities_db, type_analysis)
            end_date = DS.get_date_end(startdate, enddate, identities_db, type_analysis)

            data = dict(data.items() + init_date.items() + end_date.items())

            # Tendencies
            metrics_trends = SCR.get_metrics_core_trends()

            automator_metrics = DS.get_name()+"_metrics_trends"
            if automator_metrics in automator['r']:
                metrics_trends = automator['r'][automator_metrics].split(",")

            for i in [7,30,365]:
                for item in all_metrics:
                    if item.id not in metrics_trends: continue
                    period_data = item.get_agg_diff_days(enddate, i)
                    data = dict(data.items() +  period_data.items())

        if filter_ is not None: studies_data = {}
        else: 
            studies_data = DataSource.get_studies_data(SCR, period, startdate, enddate, evol)
        data = dict(data.items() +  studies_data.items())

        return data

    @staticmethod
    def create_agg_report (period, startdate, enddate, destdir, i_db, filter_ = None):
        data = SCR.get_agg_data (period, startdate, enddate, i_db, filter_)
        filename = SCR().get_agg_filename()
        createJSON (data, os.path.join(destdir, filename))

    @staticmethod
    def get_top_data (startdate, enddate, identities_db, filter_, npeople):
        bots = SCR.get_bots()

        top_reviewers = {}
        top_reviewers['reviewers'] = GetTopReviewersSCR(0, startdate, enddate, identities_db, bots, npeople)
        top_reviewers['reviewers.last year']= GetTopReviewersSCR(365, startdate, enddate, identities_db, bots, npeople)
        top_reviewers['reviewers.last month']= GetTopReviewersSCR(31, startdate, enddate, identities_db, bots, npeople)

        # Top openers
        top_openers = {}
        top_openers['openers.']=GetTopOpenersSCR(0, startdate, enddate,identities_db, bots, npeople)
        top_openers['openers.last year']=GetTopOpenersSCR(365, startdate, enddate,identities_db, bots, npeople)
        top_openers['openers.last_month']=GetTopOpenersSCR(31, startdate, enddate,identities_db, bots, npeople)

        # Top mergers
        top_mergers = {}
        top_mergers['mergers.last year']=GetTopMergersSCR(365, startdate, enddate,identities_db, bots, npeople)
        top_mergers['mergers.']=GetTopMergersSCR(0, startdate, enddate,identities_db, bots, npeople)
        top_mergers['mergers.last_month']=GetTopMergersSCR(31, startdate, enddate,identities_db, bots, npeople)

        # The order of the list item change so we can not check it
        top_all = dict(top_reviewers.items() +  top_openers.items() + top_mergers.items())

        return (top_all)

    @staticmethod
    def create_top_report (startdate, enddate, destdir, npeople, i_db):
        data = SCR.get_top_data (startdate, enddate, i_db, None, npeople)
        createJSON (data, destdir+"/"+SCR().get_top_filename())

    @staticmethod
    def get_filter_items(filter_, startdate, enddate, identities_db, bots):
        items = None
        filter_name = filter_.get_name()

        if (filter_name == "repository"):
            items  = GetReposSCRName(startdate, enddate)
        elif (filter_name == "company"):
            items  = GetCompaniesSCRName(startdate, enddate, identities_db)
        elif (filter_name == "country"):
            items = GetCountriesSCRName(startdate, enddate, identities_db)
        elif (filter_name == "domain"):
            logging.error("SCR " + filter_name + " not supported")
        elif (filter_name == "project"):
            items = get_projects_scr_name(startdate, enddate, identities_db)
        else:
            logging.error("SCR " + filter_name + " not supported")
        return items

    @staticmethod
    def create_filter_report(filter_, period, startdate, enddate, destdir, npeople, identities_db, bots):
        items = SCR.get_filter_items(filter_, startdate, enddate, identities_db, bots)
        if (items == None): return
        items = items['name']

        filter_name = filter_.get_name()

        if not isinstance(items, (list)):
            items = [items]

        # For repos aggregated data. Include metrics to sort in javascript.
        if (filter_name == "repository"):
            items_list = {"name":[],"review_time_days_median":[],"submitted":[]}
        else:
            items_list = items

        for item in items :
            item_file = item.replace("/","_")
            if (filter_name == "repository"):
                items_list["name"].append(item_file)

            logging.info (item)
            filter_item = Filter(filter_name, item)

            evol = SCR.get_evolutionary_data(period, startdate, enddate, 
                                               identities_db, filter_item)
            fn = os.path.join(destdir, filter_item.get_evolutionary_filename(SCR()))
            createJSON(evol, fn)

            # Static
            agg = SCR.get_agg_data(period, startdate, enddate, identities_db, filter_item)
            fn = os.path.join(destdir, filter_item.get_static_filename(SCR()))
            createJSON(agg, fn)
            if (filter_name == "repository"):
                if 'submitted' in agg: 
                    items_list["submitted"].append(agg["submitted"])
                else: items_list["submitted"].append("NA")
                if 'review_time_days_median' in agg: 
                    items_list["review_time_days_median"].append(agg['review_time_days_median'])
                else: items_list["submitted"].append("NA")

        fn = os.path.join(destdir, filter_.get_filename(SCR()))
        createJSON(items_list, fn)

    # Unify top format
    @staticmethod
    def _safeTopIds(top_data_period):
        if not isinstance(top_data_period['id'], (list)):
            for name in top_data_period:
                top_data_period[name] = [top_data_period[name]]
        return top_data_period['id']

    @staticmethod
    def get_top_people(startdate, enddate, identities_db, npeople):

        top_data = SCR.get_top_data (startdate, enddate, identities_db, None, npeople)

        top  = SCR._safeTopIds(top_data['reviewers'])
        top += SCR._safeTopIds(top_data['reviewers.last year'])
        top += SCR._safeTopIds(top_data['reviewers.last month'])
        top += SCR._safeTopIds(top_data['openers.'])
        top += SCR._safeTopIds(top_data['openers.last year'])
        top += SCR._safeTopIds(top_data['openers.last_month'])
        top += SCR._safeTopIds(top_data['mergers.'])
        top += SCR._safeTopIds(top_data['mergers.last year'])
        top += SCR._safeTopIds(top_data['mergers.last_month'])
        # remove duplicates
        people = list(set(top)) 

        return people

    @staticmethod
    def get_person_evol(upeople_id, period, startdate, enddate, identities_db, type_analysis):
        evol = GetPeopleEvolSCR(upeople_id, period, startdate, enddate)
        evol = completePeriodIds(evol, period, startdate, enddate)
        return evol

    @staticmethod
    def get_person_agg(upeople_id, startdate, enddate, identities_db, type_analysis):
        return GetPeopleStaticSCR(upeople_id, startdate, enddate)

    @staticmethod
    def create_r_reports(vizr, enddate, destdir):
        pass

    @staticmethod
    def get_query_builder():
        from query_builder import SCRQuery
        return SCRQuery

    @staticmethod
    def get_metrics_core_agg():
        m =  ['submitted','opened','closed','merged','abandoned','new','inprogress','pending','review_time','repositories']
        # patches metrics
        m += ['verified','approved','codereview','sent','WaitingForReviewer','WaitingForSubmitter']
        m += ['submitters','reviewers']

        return m

    @staticmethod
    def get_metrics_core_ts():
        m  = ['submitted','opened','closed','merged','abandoned','new','pending','review_time','repositories']
        # Get metrics using changes table for more precise results
        m += ['merged','abandoned','new']
        m += ['verified','codereview','sent','WaitingForReviewer','WaitingForSubmitter']
        m += ['submitters','reviewers']

        return m

    @staticmethod
    def get_metrics_core_trends():
        return ['submitted','merged','pending','abandoned','closed','submitters']

##########
# Specific FROM and WHERE clauses per type of report
##########
def GetSQLRepositoriesFromSCR ():
    #tables necessaries for repositories
    return (" , trackers t")

def GetSQLRepositoriesWhereSCR (repository):
    #fields necessaries to match info among tables
    return (" and t.url ='"+ repository+ "' and t.id = i.tracker_id")

def GetSQLProjectFromSCR ():
    # projects are mapped to repositories
    return (" , trackers t")

def GetSQLProjectWhereSCR (project, identities_db):
    # include all repositories for a project and its subprojects

    repos = """and t.url IN (
           SELECT repository_name
           FROM   %s.projects p, %s.project_repositories pr
           WHERE  p.project_id = pr.project_id AND p.project_id IN (%s)
               AND pr.data_source='scr'
    )""" % (identities_db, identities_db, get_subprojects(project, identities_db))

    return (repos   + " and t.id = i.tracker_id")

def GetSQLCompaniesFromSCR (identities_db):
    #tables necessaries for companies
    return (" , people_upeople pup,"+\
            identities_db+".upeople_companies upc,"+\
            identities_db+".companies c")


def GetSQLCompaniesWhereSCR (company):
    #fields necessaries to match info among tables
    return ("and i.submitted_by = pup.people_id "+\
              "and pup.upeople_id = upc.upeople_id "+\
              "and i.submitted_on >= upc.init "+\
              "and i.submitted_on < upc.end "+\
              "and upc.company_id = c.id "+\
              "and c.name ='"+ company+"'")


def GetSQLCountriesFromSCR (identities_db):
    #tables necessaries for companies
    return (" , people_upeople pup, "+\
              identities_db+".upeople_countries upc, "+\
              identities_db+".countries c ")


def GetSQLCountriesWhereSCR (country):
    #fields necessaries to match info among tables
    return ("and i.submitted_by = pup.people_id "+\
              "and pup.upeople_id = upc.upeople_id "+\
              "and upc.country_id = c.id "+\
              "and c.name ='"+country+"'")


##########
#Generic functions to obtain FROM and WHERE clauses per type of report
##########

def GetSQLReportFromSCR (identities_db, type_analysis):
    #generic function to generate 'from' clauses
    #"type" is a list of two values: type of analysis and value of
    #such analysis

    From = ""

    if (len(type_analysis) != 2): return From

    analysis = type_analysis[0]

    if (analysis):
        if analysis == 'repository': From = GetSQLRepositoriesFromSCR()
        elif analysis == 'company': From = GetSQLCompaniesFromSCR(identities_db)
        elif analysis == 'country': From = GetSQLCountriesFromSCR(identities_db)
        elif analysis == 'project': From = GetSQLProjectFromSCR()

    return (From)


def GetSQLReportWhereSCR (type_analysis, identities_db = None):
    #generic function to generate 'where' clauses

    #"type" is a list of two values: type of analysis and value of
    #such analysis

    where = ""
    if (len(type_analysis) != 2): return where

    analysis = type_analysis[0]
    value = type_analysis[1]

    if (analysis):
        if analysis == 'repository': where = GetSQLRepositoriesWhereSCR(value)
        elif analysis == 'company': where = GetSQLCompaniesWhereSCR(value)
        elif analysis == 'country': where = GetSQLCountriesWhereSCR(value)
        elif analysis == 'project':
            if (identities_db is None):
                logging.error("project filter not supported without identities_db")
                sys.exit(0)
            else:
                where = GetSQLProjectWhereSCR(value, identities_db)

    return (where)


#########
# General functions
#########

def GetReposSCRName  (startdate, enddate, limit = 0):
    limit_sql=""
    if (limit > 0): limit_sql = " LIMIT " + str(limit)

    q = "SELECT t.url as name, COUNT(DISTINCT(i.id)) AS issues "+\
           " FROM  issues i, trackers t "+\
           " WHERE i.tracker_id = t.id AND "+\
           "  i.submitted_on >="+  startdate+ " AND "+\
           "  i.submitted_on < "+ enddate +\
           " GROUP BY t.url "+\
           " ORDER BY issues DESC "+limit_sql
    names = ExecuteQuery(q)
    if not isinstance(names['name'], (list)): names['name'] = [names['name']]
    return(names)

def GetCompaniesSCRName  (startdate, enddate, identities_db, limit = 0):
    limit_sql=""
    if (limit > 0): limit_sql = " LIMIT " + str(limit)

    q = "SELECT c.id as id, c.name as name, COUNT(DISTINCT(i.id)) AS total "+\
               "FROM  "+identities_db+".companies c, "+\
                       identities_db+".upeople_companies upc, "+\
                "     people_upeople pup, "+\
                "     issues i "+\
               "WHERE i.submitted_by = pup.people_id AND "+\
               "  upc.upeople_id = pup.upeople_id AND "+\
               "  c.id = upc.company_id AND "+\
               "  i.status = 'merged' AND "+\
               "  i.submitted_on >="+  startdate+ " AND "+\
               "  i.submitted_on < "+ enddate+ " "+\
               "GROUP BY c.name "+\
               "ORDER BY total DESC " + limit_sql
    return(ExecuteQuery(q))

def GetCountriesSCRName  (startdate, enddate, identities_db, limit = 0):
    limit_sql=""
    if (limit > 0): limit_sql = " LIMIT " + str(limit)

    q = "SELECT c.name as name, COUNT(DISTINCT(i.id)) AS issues "+\
           "FROM  "+identities_db+".countries c, "+\
                   identities_db+".upeople_countries upc, "+\
            "    people_upeople pup, "+\
            "    issues i "+\
           "WHERE i.submitted_by = pup.people_id AND "+\
           "  upc.upeople_id = pup.upeople_id AND "+\
           "  c.id = upc.country_id AND "+\
           "  i.status = 'merged' AND "+\
           "  i.submitted_on >="+  startdate+ " AND "+\
           "  i.submitted_on < "+ enddate+ " "+\
           "GROUP BY c.name "+\
           "ORDER BY issues DESC "+limit_sql
    return(ExecuteQuery(q))


def get_projects_scr_name  (startdate, enddate, identities_db, limit = 0):
    # Projects activity needs to include subprojects also
    logging.info ("Getting projects list for SCR")

    # Get all projects list
    q = "SELECT p.id AS name FROM  %s.projects p" % (identities_db)
    projects = ExecuteQuery(q)
    data = []

    # Loop all projects getting reviews
    for project in projects['name']:
        type_analysis = ['project', project]
        period = None
        evol = False
        reviews = SCR.get_metrics("submitted", SCR).get_agg()
        reviews = reviews['submitted']
        if (reviews > 0):
            data.append([reviews,project])

    # Order the list using reviews: https://wiki.python.org/moin/HowTo/Sorting
    from operator import itemgetter
    data_sort = sorted(data, key=itemgetter(0),reverse=True)
    names = [name[1] for name in data_sort]

    if (limit > 0): names = names[:limit]
    return({"name":names})


# Nobody is using it yet
def GetLongestReviews  (startdate, enddate, identities_db, type_analysis = []):

#    q = "select i.issue as review, "+\
#        "         t1.old_value as patch, "+\
#        "         timestampdiff (HOUR, t1.min_time, t1.max_time) as timeOpened "+\
#        "  from ( "+\
#        "        select c.issue_id as issue_id, "+\
#        "               c.old_value as old_value, "+\
#        "               min(c.changed_on) as min_time, "+\
#        "               max(c.changed_on) as max_time "+\
#        "        from changes c, "+\
#        "             issues i "+\
#        "        where c.issue_id = i.id and "+\
#        "              i.status='NEW' "+\
#        "        group by c.issue_id, "+\
#        "                 c.old_value) t1, "+\
#        "       issues i "+\
#        "  where t1.issue_id = i.id "+\
#        "  order by timeOpened desc "+\
#        "  limit 20"
    fields = " i.issue as review, " + \
             " t1.old_value as patch, " + \
            " timestampdiff (HOUR, t1.min_time, t1.max_time) as timeOpened, "
    tables = " issues i, "+\
            " (select c.issue_id as issue_id, "+\
            "           c.old_value as old_value, "+\
            "           min(c.changed_on) as min_time, "+\
            "           max(c.changed_on) as max_time "+\
            "    from changes c, "+\
            "         issues i "+\
            "    where c.issue_id = i.id and "+\
            "          i.status='NEW' "+\
            "    group by c.issue_id, "+\
            "             c.old_value) t1 "
    tables = tables + GetSQLReportFromSCR(identities_db, type_analysis)
    filters = " t1.issue_id = i.id "
    filters = filters + GetSQLReportWhereSCR(type_analysis, identities_db)

    q = GetSQLGlobal(" i.submitted_on ", fields, tables, filters,
                           startdate, enddate)

    return(ExecuteQuery(q))

##
# Tops
##

# Is this right???
def GetTopReviewersSCR (days, startdate, enddate, identities_db, bots, limit):
    date_limit = ""
    filter_bots = ''
    for bot in bots:
        filter_bots = filter_bots + " up.identifier<>'"+bot+"' and "

    if (days != 0 ):
        q = "SELECT @maxdate:=max(changed_on) from changes limit 1"
        ExecuteQuery(q)
        date_limit = " AND DATEDIFF(@maxdate, changed_on)<" + str(days)

    q = "SELECT up.id as id, up.identifier as reviewers, "+\
        "               count(distinct(c.id)) as reviewed "+\
        "        FROM people_upeople pup, changes c, "+ identities_db+".upeople up "+\
        "        WHERE "+ filter_bots+ " "+\
        "            c.changed_by = pup.people_id and "+\
        "            pup.upeople_id = up.id and "+\
        "            c.changed_on >= "+ startdate + " and "+\
        "            c.changed_on < "+ enddate + " "+\
        "            "+ date_limit + " "+\
        "        GROUP BY up.identifier "+\
        "        ORDER BY reviewed desc, reviewers "+\
        "        LIMIT " + limit
    return(ExecuteQuery(q))


def GetTopSubmittersQuerySCR   (days, startdate, enddate, identities_db, bots, limit, merged = False):
    date_limit = ""
    merged_sql = ""
    rol = "openers"
    action = "opened"
    filter_bots = ''
    for bot in bots:
        filter_bots = filter_bots+ " up.identifier<>'"+bot+"' and "

    if (days != 0 ):
        q = "SELECT @maxdate:=max(submitted_on) from issues limit 1"
        ExecuteQuery(q)
        date_limit = " AND DATEDIFF(@maxdate, submitted_on)<"+str(days)

    if (merged):
        merged_sql = " AND status='MERGED' "
        rol = "mergers"
        action = "merged"


    q = "SELECT up.id as id, up.identifier as "+rol+", "+\
        "            count(distinct(i.id)) as "+action+" "+\
        "        FROM people_upeople pup, issues i, "+identities_db+".upeople up "+\
        "        WHERE "+ filter_bots+ " "+\
        "            i.submitted_by = pup.people_id and "+\
        "            pup.upeople_id = up.id and "+\
        "            i.submitted_on >= "+ startdate+ " and "+\
        "            i.submitted_on < "+ enddate+ " "+\
        "            "+date_limit+ merged_sql+ " "+\
        "        GROUP BY up.identifier "+\
        "        ORDER BY "+action+" desc, id "+\
        "        LIMIT "+ limit
    return(q)


def GetTopOpenersSCR (days, startdate, enddate, identities_db, bots, limit):
    q = GetTopSubmittersQuerySCR (days, startdate, enddate, identities_db, bots, limit)
    return(ExecuteQuery(q))


def GetTopMergersSCR   (days, startdate, enddate, identities_db, bots, limit):
    q = GetTopSubmittersQuerySCR (days, startdate, enddate, identities_db, bots, limit, True)
    return(ExecuteQuery(q))


#########
# PEOPLE: Pretty similar to ITS
#########
def GetTablesOwnUniqueIdsSCR (table=''):
    tables = 'changes c, people_upeople pup'
    if (table == "issues"): tables = 'issues i, people_upeople pup'
    return (tables)


def GetFiltersOwnUniqueIdsSCR  (table=''):
    filters = 'pup.people_id = c.changed_by'
    if (table == "issues"): filters = 'pup.people_id = i.submitted_by'
    return (filters)


def GetPeopleListSCR (startdate, enddate, bots):

    filter_bots = ""
    for bot in bots:
        filter_bots += " name<>'"+bot+"' and "

    fields = "DISTINCT(pup.upeople_id) as id, count(i.id) as total, name"
    tables = GetTablesOwnUniqueIdsSCR('issues') + ", people"
    filters = filter_bots
    filters += GetFiltersOwnUniqueIdsSCR('issues')+ " and people.id = pup.people_id"
    filters += " GROUP BY id ORDER BY total desc"
    q = GetSQLGlobal('submitted_on', fields, tables, filters, startdate, enddate)
    return(ExecuteQuery(q))

def GetPeopleQuerySCRChanges (developer_id, period, startdate, enddate, evol):
    fields = "COUNT(c.id) AS changes"
    tables = GetTablesOwnUniqueIdsSCR()
    filters = GetFiltersOwnUniqueIdsSCR()+ " AND pup.upeople_id = "+ str(developer_id)

    if (evol):
        q = GetSQLPeriod(period,'changed_on', fields, tables, filters,
                startdate, enddate)
    else:
        fields = fields + \
                ",DATE_FORMAT (min(changed_on),'%Y-%m-%d') as first_date, "+\
                "  DATE_FORMAT (max(changed_on),'%Y-%m-%d') as last_date"
        q = GetSQLGlobal('changed_on', fields, tables, filters,
                startdate, enddate)
    return (q)

def GetPeopleQuerySCR (developer_id, period, startdate, enddate, evol):
    fields = "COUNT(c.id) AS closed"
    tables = GetTablesOwnUniqueIdsSCR()
    filters = GetFiltersOwnUniqueIdsSCR()+ " AND pup.upeople_id = "+ str(developer_id)

    if (evol):
        q = GetSQLPeriod(period,'changed_on', fields, tables, filters,
                startdate, enddate)
    else:
        fields = fields + \
                ",DATE_FORMAT (min(changed_on),'%Y-%m-%d') as first_date, "+\
                "  DATE_FORMAT (max(changed_on),'%Y-%m-%d') as last_date"
        q = GetSQLGlobal('changed_on', fields, tables, filters,
                startdate, enddate)
    return (q)

def GetPeopleQuerySCRSubmissions (developer_id, period, startdate, enddate, evol):
    fields = "COUNT(i.id) AS submissions"
    tables = GetTablesOwnUniqueIdsSCR('issues')
    filters = GetFiltersOwnUniqueIdsSCR('issues')+ " AND pup.upeople_id = "+ str(developer_id)

    if (evol):
        q = GetSQLPeriod(period,'submitted_on', fields, tables, filters,
                startdate, enddate)
    else:
        fields = fields + \
                ",DATE_FORMAT (min(submitted_on),'%Y-%m-%d') as first_date, "+\
                "  DATE_FORMAT (max(submitted_on),'%Y-%m-%d') as last_date"
        q = GetSQLGlobal('submitted_on', fields, tables, filters,
                startdate, enddate)
    return (q)



def GetPeopleEvolSCR (developer_id, period, startdate, enddate):
    # q = GetPeopleQuerySCRSubmissions(developer_id, period, startdate, enddate, True)
    q = GetPeopleQuerySCR(developer_id, period, startdate, enddate, True)
    return(ExecuteQuery(q))

def GetPeopleStaticSCR (developer_id, startdate, enddate):
    # q = GetPeopleQuerySCRSubmissions(developer_id, None, startdate, enddate, False)
    q = GetPeopleQuerySCR(developer_id, None, startdate, enddate, False)
    return(ExecuteQuery(q))