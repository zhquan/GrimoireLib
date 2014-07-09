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
## This file is a part of GrimoireLib
##  (an Python library for the MetricsGrimoire and vizGrimoire systems)
##
##
## Authors:
##   Alvaro del Castillo <acs@bitergia.com>

""" Metrics for the source code review system """

import logging
import MySQLdb

from GrimoireUtils import completePeriodIds, checkListArray, medianAndAvgByPeriod

from metrics import Metrics

from metrics_filter import MetricFilters

from query_builder import ITSQuery

from SCR import SCR

class Submitted(Metrics):
    id = "submitted"
    name = "Submitted reviews"
    desc = "Number of submitted code review processes"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetReviewsSQL(self.filters.period, self.filters.startdate,
                                  self.filters.enddate, "submitted",
                                  self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

class Merged(Metrics):
    id = "merged"
    name = "Merged changes"
    desc = "Number of changes merged into the source code"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetReviewsSQL(self.filters.period, self.filters.startdate,
                                  self.filters.enddate, "merged",
                                  self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

    def __get_sql__changes (self, evolutionary):
        q = self.db.GetReviewsChangesSQL(self.filters.period, self.filters.startdate,
                                         self.filters.enddate, "merged",
                                         self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

    def get_ts_changes(self):
        query = self.__get_sql__changes(True)
        ts = self.db.ExecuteQuery(query)
        return completePeriodIds(ts, self.filters.period,
                                 self.filters.startdate, self.filters.enddate)


class Mergers(Metrics):
    id = "mergers"
    name = "Successful submitters"
    desc = "Number of persons submitting changes that got accepted"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        pass

class Abandoned(Metrics):
    id = "abandoned"
    name = "Abandoned reviews"
    desc = "Number of abandoned review processes"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetReviewsSQL(self.filters.period, self.filters.startdate,
                                  self.filters.enddate, "abandoned",
                                  self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

    def __get_sql__changes (self, evolutionary):
        q = self.db.GetReviewsChangesSQL(self.filters.period, self.filters.startdate,
                                         self.filters.enddate, "abandoned",
                                         self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

    def get_ts_changes(self):
        query = self.__get_sql__changes(True)
        ts = self.db.ExecuteQuery(query)
        return completePeriodIds(ts, self.filters.period,
                                 self.filters.startdate, self.filters.enddate)

class Pending(Metrics):
    id = "pending"
    name = "Pending reviews"
    desc = "Number of pending review processes"
    data_source = SCR


    def _get_metrics_for_pending(self):
        # We need to fix the same filter for all metrics
        metrics_for_pendig = {}

        metric = SCR.get_metrics("submitted", SCR)
        metric.filters = self.filters
        metrics_for_pendig['submitted'] = metric

        metric = SCR.get_metrics("merged", SCR)
        metric.filters = self.filters
        metrics_for_pendig['merged'] = metric

        metric = SCR.get_metrics("abandoned", SCR)
        metric.filters = self.filters
        metrics_for_pendig['abandoned'] = metric

        return metrics_for_pendig


    def get_agg(self):
        metrics = self._get_metrics_for_pending()
        submitted = metrics['submitted'].get_agg()
        merged = metrics['merged'].get_agg()
        abandoned = metrics['abandoned'].get_agg()

        pending = submitted['submitted']-merged['merged']-abandoned['abandoned']
        return ({"pending":pending})

    def get_ts(self):
        metrics = self._get_metrics_for_pending()
        submitted = metrics["submitted"].get_ts()
        merged = metrics["merged"].get_ts()
        abandoned = metrics["abandoned"].get_ts()
        evol = dict(submitted.items() + merged.items() + abandoned.items())
        pending = {"pending":[]}
        for i in range(0, len(evol['submitted'])):
            pending_val = evol["submitted"][i] - evol["merged"][i] - evol["abandoned"][i]
            pending["pending"].append(pending_val)
        pending[self.filters.period] = evol[self.filters.period]
        return pending

class Opened(Metrics):
    id = "opened"
    name = "Opened reviews"
    desc = "Number of review processes opened"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetReviewsSQL(self.filters.period, self.filters.startdate,
                                  self.filters.enddate, "opened",
                                  self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

class Closed(Metrics):
    id = "closed"
    name = "Closed reviews"
    desc = "Number of closed review processes (merged or abandoned)"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetReviewsSQL(self.filters.period, self.filters.startdate,
                                  self.filters.enddate, "closed",
                                  self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

class InProgress(Metrics):
    id = "inprogress"
    name = "In progress reviews"
    desc = "Number review processes in progress"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetReviewsSQL(self.filters.period, self.filters.startdate,
                                  self.filters.enddate, "inprogress",
                                  self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q


class New(Metrics):
    id = "new"
    name = "New reviews"
    desc = "Number of new review processes"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetReviewsSQL(self.filters.period, self.filters.startdate,
                                  self.filters.enddate, "new",
                                  self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

    def __get_sql__changes (self, evolutionary):
        q = self.db.GetReviewsChangesSQL(self.filters.period, self.filters.startdate,
                                         self.filters.enddate, "new",
                                         self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

    def get_ts_changes(self):
        query = self.__get_sql__changes(True)
        ts = self.db.ExecuteQuery(query)
        return completePeriodIds(ts, self.filters.period,
                                 self.filters.startdate, self.filters.enddate)

class PatchesVerified(Metrics):
    id = "verified"
    name = "Verified patches reviews"
    desc = "Number of verified review processes"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetEvaluationsSQL (self.filters.period, self.filters.startdate,
                                       self.filters.enddate, "verified",
                                       self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

class PatchesApproved(Metrics):
    id = "approved"
    name = "Approved patches reviews"
    desc = "Number of approved review processes"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetEvaluationsSQL (self.filters.period, self.filters.startdate,
                                       self.filters.enddate, "approved",
                                       self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

class PatchesCodeReview(Metrics):
    id = "codereview"
    name = "Code review patches"
    desc = "Number of patches in review processes in code review state"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetEvaluationsSQL (self.filters.period, self.filters.startdate,
                                       self.filters.enddate, "codereview",
                                       self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

class PatchesSent(Metrics):
    id = "sent"
    name = "Number of patches sent"
    desc = "Number of patches sent"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetEvaluationsSQL (self.filters.period, self.filters.startdate,
                                       self.filters.enddate, "sent",
                                       self.filters.type_analysis, evolutionary, self.db.identities_db)
        return q

class PatchesWaitingForReviewer(Metrics):
    id = "WaitingForReviewer"
    name = "Waiting for reviewer patches"
    desc = "Number of patches from review processes waiting for reviewer"
    data_source = SCR


    def __get_sql__(self, evolutionary):
        q = self.db.GetWaiting4ReviewerSQL(self.filters.period, self.filters.startdate,
                                           self.filters.enddate, self.db.identities_db,
                                           self.filters.type_analysis, evolutionary)
        return q

class PatchesWaitingForSubmitter(Metrics):
    id = "WaitingForSubmitter"
    name = "Waiting for submitter patches"
    desc = "Number of patches from review processes waiting for submitter"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q = self.db.GetWaiting4SubmitterSQL(self.filters.period, self.filters.startdate,
                                            self.filters.enddate, self.db.identities_db,
                                            self.filters.type_analysis, evolutionary)
        return q

class ReviewsWaitingForReviewer(Metrics):
    id = "ReviewsWaitingForReviewer"
    name = "Reviews waiting for reviewer"
    desc = "Number of preview processes waiting for reviewer"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        q_last_change = self.db.get_sql_last_change_for_issues_new()

        fields = "COUNT(DISTINCT(i.id)) as ReviewsWaitingForReviewer"
        tables = "changes c, issues i, (%s) t1" % q_last_change
        tables += self.db.GetSQLReportFrom(self.db.identities_db, self.filters.type_analysis)
        filters = """
            i.id = c.issue_id  AND t1.id = c.id
            AND (c.field='CRVW' or c.field='Code-Review' or c.field='Verified' or c.field='VRIF')
            AND (c.new_value=1 or c.new_value=2)
        """
        filters = filters + self.db.GetSQLReportWhere(self.filters.type_analysis, self.db.identities_db)

        q = self.db.BuildQuery (self.filters.period, self.filters.startdate,
                                self.filters.enddate, " c.changed_on",
                                fields, tables, filters, evolutionary)
        return(q)


class ReviewsWaitingForSubmitter(Metrics):
    id = "ReviewsWaitingForSubmitter"
    name = "Reviews waiting for submitter"
    desc = "Number of review processes waiting for submitter"
    data_source = SCR


    def __get_sql__(self, evolutionary):
        q_last_change = self.db.get_sql_last_change_for_issues_new()

        fields = "COUNT(DISTINCT(i.id)) as ReviewsWaitingForSubmitter"
        tables = "changes c, issues i, (%s) t1" % q_last_change
        tables += self.db.GetSQLReportFrom(self.db.identities_db, self.filters.type_analysis)
        filters = """
            i.id = c.issue_id  AND t1.id = c.id
            AND (c.field='CRVW' or c.field='Code-Review' or c.field='Verified' or c.field='VRIF')
            AND (c.new_value=-1 or c.new_value=-2)
        """
        filters = filters + self.db.GetSQLReportWhere(self.filters.type_analysis, self.db.identities_db)

        q = self.db.BuildQuery (self.filters.period, self.filters.startdate,
                                self.filters.enddate, " c.changed_on",
                                fields, tables, filters, evolutionary)
        return q

class Companies(Metrics):
    id = "companies"
    name = "Organizations"
    desc = "Number of organizations (companies, etc.) with persons active in code review"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        fields = "count(distinct(upc.company_id)) as companies"
        tables = "issues i, people_upeople pup, %s.upeople_companies upc" % (self.db.identities_db)
        filters = "i.submitted_by = pup.people_id and pup.upeople_id = upc.upeople_id"

        q = self.db.BuildQuery (self.filters.period, self.filters.startdate,
                                self.filters.enddate, " i.submitted_on",
                                fields, tables, filters, evolutionary)
        return q

class Countries(Metrics):
    id = "countries"
    name = "Countries"
    desc = "Number of countries with persons active in code review"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        fields = "count(distinct(upc.country_id)) as countries"
        tables = "issues i, people_upeople pup, %s.upeople_countries upc" % (self.db.identities_db)
        filters = "i.submitted_by = pup.people_id and pup.upeople_id = upc.upeople_id"

        q = self.db.BuildQuery (self.filters.period, self.filters.startdate,
                                self.filters.enddate, " i.submitted_on",
                                fields, tables, filters, evolutionary)
        return q

class Domains(Metrics):
    id = "domains"
    name = "Domains"
    desc = "Number of domains with persons active in code review"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        pass

class Repositories(Metrics):
    id = "repositories"
    name = "Repositories"
    desc = "Number of repositories with persons active in code review"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        fields = "count(distinct(t.id)) as repositories"
        tables = "issues i, trackers t"
        filters = "i.tracker_id = t.id"
        q = self.db.BuildQuery (self.filters.period, self.filters.startdate,
                                self.filters.enddate, " i.submitted_on",
                                fields, tables, filters, evolutionary)
        return q

class People(Metrics):
    id = "people"
    name = "People"
    desc = "Number of persons active in code review activities"
    data_source = SCR

    def __get_sql__(self, evolutionary):
        pass

class Reviewers(Metrics):
    id = "reviewers"
    name = "Reviewers"
    desc = "Number of persons reviewing code review activities"
    data_source = SCR
    action = "reviews"

    # Not sure if this top is right
    def _get_top_global (self, days = 0, metric_filters = None):
        if metric_filters == None:
            metric_filters = self.filters

        startdate = metric_filters.startdate
        enddate = metric_filters.enddate
        limit = metric_filters.npeople
        filter_bots = self.get_bots_filter_sql(metric_filters)
        if filter_bots != "": filter_bots += " AND "
        date_limit = ""


        if (days != 0 ):
            q = "SELECT @maxdate:=max(changed_on) from changes limit 1"
            self.db.ExecuteQuery(q)
            date_limit = " AND DATEDIFF(@maxdate, changed_on)<" + str(days)

        q = "SELECT u.id as id, u.identifier as reviewers, "+\
            "               count(distinct(c.id)) as reviewed "+\
            "        FROM people_upeople pup, changes c, "+ self.db.identities_db+".upeople u "+\
            "        WHERE "+ filter_bots+ " "+\
            "            c.changed_by = pup.people_id and "+\
            "            pup.upeople_id = u.id and "+\
            "            c.changed_on >= "+ startdate + " and "+\
            "            c.changed_on < "+ enddate + " "+\
            "            "+ date_limit + " "+\
            "        GROUP BY u.identifier "+\
            "        ORDER BY reviewed desc, reviewers "+\
            "        LIMIT " + str(limit)
        return(self.db.ExecuteQuery(q))



    def __get_sql__(self, evolutionary):
        fields = " count(distinct(changed_by)) as reviewers "
        tables = " changes c "
        filters = ""

        q = self.db.BuildQuery (self.filters.period, self.filters.startdate,
                                self.filters.enddate, " c.changed_on",
                                fields, tables, filters, evolutionary)
        return q

class Closers(Metrics):
    id = "closers"
    name = "Closers"
    desc = "Number of persons closing code review activities"
    data_source = SCR
    action = "closed"

    def _get_top_global (self, days = 0, metric_filters = None):

        if metric_filters == None:
            metric_filters = self.filters

        startdate = metric_filters.startdate
        enddate = metric_filters.enddate
        limit = metric_filters.npeople
        filter_bots = self.get_bots_filter_sql(metric_filters)
        if filter_bots != "": filter_bots += " AND "
        date_limit = ""

        if (days != 0 ):
            q = "SELECT @maxdate:=max(submitted_on) from issues limit 1"
            self.db.ExecuteQuery(q)
            date_limit = " AND DATEDIFF(@maxdate, submitted_on)<"+str(days)


        merged_sql = " AND status='MERGED' "
        rol = "mergers"
        action = "merged"

        q = "SELECT u.id as id, u.identifier as "+rol+", "+\
            "            count(distinct(i.id)) as "+action+" "+\
            "        FROM people_upeople pup, issues i, "+self.db.identities_db+".upeople u "+\
            "        WHERE "+ filter_bots+ " "+\
            "            i.submitted_by = pup.people_id and "+\
            "            pup.upeople_id = u.id and "+\
            "            i.submitted_on >= "+ startdate+ " and "+\
            "            i.submitted_on < "+ enddate+ " "+\
            "            "+date_limit+ merged_sql+ " "+\
            "        GROUP BY u.identifier "+\
            "        ORDER BY "+action+" desc, id "+\
            "        LIMIT "+ str(limit)
        return(self.db.ExecuteQuery(q))


    def __get_sql__(self, evolutionary):
        pass

# Pretty similar to ITS openers
class Submitters(Metrics):
    id = "submitters"
    name = "Submitters"
    desc = "Number of persons submitting code review processes"
    data_source = SCR
    action = "submitted"

    def __get_sql_trk_prj__(self, evolutionary):
        """ First we get the submitters then join with unique identities """
        tpeople_sql  = "SELECT  distinct(submitted_by) as submitted_by, submitted_on  "
        tpeople_sql += " FROM issues i " + self.db.GetSQLReportFrom(self.db.identities_db, self.filters.type_analysis)
        filters_ext = self.db.GetSQLReportWhere(self.filters.type_analysis, self.db.identities_db) 
        if (filters_ext != ""):
            # Hack: remove "and "
            filters_ext = filters_ext[4:]
            tpeople_sql += " WHERE " + filters_ext


        fields = " count(distinct(upeople_id)) as submitters "
        tables = " people_upeople pup, (%s) tpeople " % (tpeople_sql)
        filters = " tpeople.submitted_by = pup.people_id "

        q = self.db.BuildQuery(self.filters.period, self.filters.startdate,
                               self.filters.enddate, " tpeople.submitted_on ",
                               fields, tables, filters, evolutionary)
        return q


    def __get_sql_default__(self, evolutionary):
        """ This function returns the evolution or agg number of people opening issues """
        fields = " count(distinct(pup.upeople_id)) as submitters "
        tables = " issues i " + self.db.GetSQLReportFrom(self.db.identities_db, self.filters.type_analysis)
        filters = self.db.GetSQLReportWhere(self.filters.type_analysis, self.db.identities_db)

        if (self.filters.type_analysis is None or len (self.filters.type_analysis) != 2) :
            #Specific case for the basic option where people_upeople table is needed
            #and not taken into account in the initial part of the query
            tables += ", people_upeople pup"
            filters += " and i.submitted_by = pup.people_id"
        elif (self.filters.type_analysis[0] == "repository" or self.filters.type_analysis[0] == "project"):
            #Adding people_upeople table
            tables += ", people_upeople pup"
            filters += " and i.submitted_by = pup.people_id "

        q = self.db.BuildQuery(self.filters.period, self.filters.startdate,
                               self.filters.enddate, " submitted_on ",
                               fields, tables, filters, evolutionary)
        return q

    def __get_sql__(self, evolutionary):
        if (self.filters.type_analysis is not None and (self.filters.type_analysis[0] in  ["repository","project"])):
            return self.__get_sql_trk_prj__(evolutionary)
        else:
            return self.__get_sql_default__(evolutionary)

    def _get_top_global (self, days = 0, metric_filters = None):
        if metric_filters == None:
            metric_filters = self.filters
        startdate = metric_filters.startdate
        enddate = metric_filters.enddate
        limit = metric_filters.npeople
        filter_bots = self.get_bots_filter_sql(metric_filters)
        if filter_bots != "": filter_bots += " AND "

        date_limit = ""
        rol = "openers"
        action = "opened"

        if (days != 0 ):
            q = "SELECT @maxdate:=max(submitted_on) from issues limit 1"
            self.db.ExecuteQuery(q)
            date_limit = " AND DATEDIFF(@maxdate, submitted_on)<"+str(days)

        q = "SELECT u.id as id, u.identifier as "+rol+", "+\
            "            count(distinct(i.id)) as "+action+" "+\
            "        FROM people_upeople pup, issues i, "+self.db.identities_db+".upeople u "+\
            "        WHERE "+ filter_bots+ " "+\
            "            i.submitted_by = pup.people_id and "+\
            "            pup.upeople_id = u.id and "+\
            "            i.submitted_on >= "+ startdate+ " and "+\
            "            i.submitted_on < "+ enddate+ " "+\
            "            "+date_limit +  " "+\
            "        GROUP BY u.identifier "+\
            "        ORDER BY "+action+" desc, id "+\
            "        LIMIT "+ str(limit)
        return(self.db.ExecuteQuery(q))

class TimeToReview(Metrics):
    id = "review_time"
    name = "Review Time"
    desc = "Time to review"
    data_source = SCR

    def __get_sql__(self):
        if self.filters.period != "month": return None
        bots = []
        q = self.db.GetTimeToReviewQuerySQL (self.filters.startdate, self.filters.enddate,
                                             self.db.identities_db, self.filters.type_analysis, bots)
        return q

    def get_agg(self):
        from numpy import median, average
        from GrimoireUtils import removeDecimals

        q = self.__get_sql__()
        if q is None: return {}
        data = self.db.ExecuteQuery(q)
        data = data['revtime']
        if (isinstance(data, list) == False): data = [data]
        # ttr_median = sorted(data)[len(data)//2]
        if (len(data) == 0):
            ttr_median = float("nan")
            ttr_avg = float("nan")
        else:
            ttr_median = float(median(removeDecimals(data)))
            ttr_avg = float(average(removeDecimals(data)))
        return {"review_time_days_median":ttr_median, "review_time_days_avg":ttr_avg}

    def get_ts(self):
        q = self.__get_sql__()
        if q is None: return {}
        review_list = self.db.ExecuteQuery(q)
        checkListArray(review_list)
        metrics_list = {}


        med_avg_list = medianAndAvgByPeriod(self.filters.period, review_list['changed_on'], review_list['revtime'])
        if (med_avg_list != None):
            metrics_list['review_time_days_median'] = med_avg_list['median']
            metrics_list['review_time_days_avg'] = med_avg_list['avg']
            metrics_list['month'] = med_avg_list['month']
        else:
            metrics_list['review_time_days_median'] = []
            metrics_list['review_time_days_avg'] = []
            metrics_list['month'] = []

        metrics_list = completePeriodIds(metrics_list, self.filters.period,
                          self.filters.startdate, self.filters.enddate)

        return metrics_list
