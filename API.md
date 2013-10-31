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
