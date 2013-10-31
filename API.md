The War Chest API provides campaign finance information for Chicago aldermen.

To access the API call http://chicagoelections.datamade.us/war-chest/

You'll receive back a JSON array of objects describing aldermen's campaign committees and finances.

```json
[

    {
        "pupa_id": "ocd-person/94674f56-3cec-11e3-8a24-22000a971dca",
        "active_committees": [
            {
                "committee_url": "http://www.elections.il.gov/CampaignDisclosure/CommitteeDetail.aspx?id=6380",
                "current_funds": 61749.55,
                "name": "Citizens for Joe Moore",
                "date_filed": "2013-04-24T15:23:05",
                "reporting_period_end": "2013-03-31",
                "last_cycle_receipts": 86600,
                "latest_report_url": "http://www.elections.il.gov/CampaignDisclosure/D2Quarterly.aspx?id=500538",
                "last_cycle_expenditures": 45266.07
            }
        ],
        "candidate": "Joseph A Moore"
    },
    ...
]
```

Each object has three fields: `pupa_id`, `active_committees`, and `candidate`. The value of `candidate` is the name of candidate.
The value of `pupa_id` is a unique key for this **person** that we use across the APIs. 

The value of `active_committees` is an array of objects, where each object contains information about a candidate committee. Some
candidates have more than one committeee.

A committee object has eight fields: `committee_url`, `current_funds`, `name`, `date_filed`, `reporting_period_end`, 
`last_cycle_receipts`, `latest_report_url`, and `last_cycle_expenditure`. 

`committee_url` is the url for the committee's page on the Illinois State Board of Elections. 

`name` is the name of the committee

`latest_report_url` is the url for the last campaign finance report available on Illinois State Board of Elections

`reporting_period_end` is the end of the reporting period for the latest campaign finance report

`current_funds` is the current funds of the committee as of the end of the `reporting_period_end`

`last_cycle_receipts` and `last_cycle_expenditures` will correspond to the amount that came in and went out during
the last campaign cycle. This is a little broken now.

