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
## Reporting of some metrics for a proposed maturity model for projects.
##
## Authors:
##   Jesus M. Gonzalez-Barahona <jgb@bitergia.com>
##

from datetime import datetime, timedelta

analysis_date = datetime(2014,2,1)

# Dictionary to store values for maturity metrics 
values = {}
# Dictionary to store time series for maturity metrics
timeseries = {}

if __name__ == "__main__":

    from grimoirelib_alch.query.scm import DB as SCMDatabase
    from grimoirelib_alch.family.scm import (
        SCM, NomergesCondition, PeriodCondition, BranchesCondition
        )
    from grimoirelib_alch.aux.standalone import stdout_utf8, print_banner
    from grimoirelib_alch.aux.reports import create_report

    from sqlalchemy import func, and_
    from sqlalchemy.sql import label

    stdout_utf8()

    prefix = "maturity-"
    database = SCMDatabase (url = "mysql://jgb:XXX@localhost/",
                   schema = "vizgrimoire_cvsanaly",
                   schema_id = "vizgrimoire_cvsanaly")
    session = database.build_session()

    month_end = analysis_date
    month_start = analysis_date - timedelta(days=30)
    scm_repos_name = ['VizGrimoireJS.git', 'VizGrimoireJS-lib.git'] 

    query = session.query(
        label("id", SCMDatabase.Repositories.id)
        ) \
        .filter (SCMDatabase.Repositories.name.in_ (scm_repos_name))
    scm_repos = [row.id for row in query.all()]
    print scm_repos

    #---------------------------------
    print_banner ("SCM_COMMITS_1M: Number of commits during last month")
    nomerges = NomergesCondition()
    last_month = PeriodCondition (start = month_start,
                                  end = month_end,
                                  date = "author"
                                  )
    master = BranchesCondition (branches = ("master",))
    ncommits = SCM (datasource = session,
                    name = "ncommits",
                    conditions = (nomerges, last_month, master))
    values ["scm_commits_1m"] = ncommits.total()
    ncommits = SCM (datasource = session,
                name = "ncommits",
                conditions = (nomerges, master))
    timeseries ["scm_commits_1m"] = ncommits.timeseries()

    #---------------------------------
    print_banner ("SCM_FILES_1M: Number of files during last month")

    query = session.query(
        label(
            "files",
            func.count (func.distinct(SCMDatabase.Actions.file_id))
            )
        ) \
        .join (SCMDatabase.SCMLog) \
        .filter(and_(
                SCMDatabase.SCMLog.author_date > month_start,
                SCMDatabase.SCMLog.author_date <= month_end,
                SCMDatabase.SCMLog.repository_id.in_ (scm_repos)
                ))
    values ["scm_files_1m"] = query.one().files

    report = {
        prefix + 'values.json': values,
        prefix + 'timeseries.json': timeseries,
        }

    create_report (report_files = report, destdir = '/tmp/')
