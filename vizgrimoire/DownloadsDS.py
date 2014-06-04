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
## Authors:
##   Daniel Izquierdo <dizquierdo@bitergia.com>
##   Alvaro del Castillo <acs@bitergia.com>


# All of the functions found in this file expect to find a database
# with the followin format:
# Table: downloads
#       Fields: date (datetime), ip (varchar), package (varchar), protocol (varchar)
#       

import logging, os

from GrimoireSQL import ExecuteQuery, BuildQuery
from GrimoireUtils import completePeriodIds, createJSON

from data_source import DataSource

from metrics_filter import MetricFilters


class DownloadsDS(DataSource):
    _metrics_set = []

    @staticmethod
    def get_db_name():
        return "db_downloads"

    @staticmethod
    def get_name(): return "downloads"

    @staticmethod
    def _get_data (period, startdate, enddate, i_db, filter_, evol):
        data = {}

        type_analysis = None
        if (filter_ is not None):
            type_analysis = [filter_.get_name(), filter_.get_item()]
            logging.warn("DownloadsDS does not support filters.")
            return data

        metrics_on = ['downloads','packages','protocols','ips']
        mfilter = MetricFilters(period, startdate, enddate, type_analysis)
        all_metrics = DownloadsDS.get_metrics_set(DownloadsDS)

        for item in all_metrics:
            if item.id not in metrics_on: continue
            item.filters = mfilter
            if evol is False:
                mvalue = item.get_agg()
            else:
                mvalue = item.get_ts()
            data = dict(data.items() + mvalue.items())

            if evol is False:
                # Tendencies
                metrics_trends = ['downloads','packages']

                for i in [7,30,365]:
                    for item in all_metrics:
                        if item.id not in metrics_trends: continue
                        period_data = item.get_agg_diff_days(enddate, i)
                        data = dict(data.items() +  period_data.items())
        return data

    @staticmethod
    def get_evolutionary_data (period, startdate, enddate, i_db, filter_ = None):
        return DownloadsDS._get_data(period, startdate, enddate, i_db, filter_, True)

    @staticmethod
    def create_evolutionary_report (period, startdate, enddate, destdir, i_db, filter_ = None):
        data =  DownloadsDS.get_evolutionary_data (period, startdate, enddate, i_db, filter_)
        filename = DownloadsDS().get_evolutionary_filename()
        createJSON (data, os.path.join(destdir, filename))

    @staticmethod
    def get_agg_data (period, startdate, enddate, i_db, filter_ = None):
        return DownloadsDS._get_data(period, startdate, enddate, i_db, filter_, False)

    @staticmethod
    def create_agg_report (period, startdate, enddate, destdir, i_db, filter_ = None):
        data = DownloadsDS.get_agg_data (period, startdate, enddate, i_db, filter_)
        filename = DownloadsDS().get_agg_filename()
        createJSON (data, os.path.join(destdir, filename))

    @staticmethod
    def get_top_data (startdate, enddate, identities_db, filter_ = None, npeople = None):
        top20 = {}
        top20['ips.'] = TopIPs(startdate, enddate, 20)
        top20['packages.'] = TopPackages(startdate, enddate, 20)
        return top20


    @staticmethod
    def create_top_report (startdate, enddate, destdir, npeople, i_db):
        data = DownloadsDS.get_top_data (startdate, enddate, i_db, None, npeople)
        top_file = destdir+"/"+DownloadsDS().get_top_filename()
        createJSON (data, top_file)

    @staticmethod
    def get_filter_items(filter_, startdate, enddate, identities_db, bots):
        items = None
        filter_name = filter_.get_name()

        logging.error("DownloadsDS " + filter_name + " not supported")
        return items

    @staticmethod
    def create_filter_report(filter_, period, startdate, enddate, destdir, npeople, identities_db, bots):
        items = DownloadsDS.get_filter_items(filter_, startdate, enddate, identities_db, bots)
        if (items == None): return

    @staticmethod
    def get_top_people(startdate, enddate, identities_db, npeople):
        pass

    @staticmethod
    def get_person_evol(upeople_id, period, startdate, enddate, identities_db, type_analysis):
        pass

    @staticmethod
    def get_person_agg(upeople_id, startdate, enddate, identities_db, type_analysis):
        pass

    @staticmethod
    def create_r_reports(vizr, enddate, destdir):
        pass

    @staticmethod
    def get_metrics_definition ():
        pass

    @staticmethod
    def get_query_builder ():
        from query_builder import DownloadsDSQuery
        return DownloadsDSQuery

def TopIPs(startdate, enddate, numTop):
    # Top IPs downloading packages in a given period
    query = """
            select ip as ips, count(*) as downloads 
            from downloads
            where date >= %s and
                  date < %s
            group by ips
            order by downloads desc
            limit %s
            """ % (startdate, enddate, str(numTop))
    return ExecuteQuery(query)

def TopPackages(startdate, enddate, numTop):
    # Top Packages bein downloaded in a given period
    query = """
            select package as packages, count(*) as downloads
            from downloads
            where date >= %s and
                  date < %s
            group by packages
            order by downloads desc
            limit %s
            """ % (startdate, enddate, str(numTop))
    return ExecuteQuery(query)