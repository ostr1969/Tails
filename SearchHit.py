from copy import deepcopy
from dataclasses import dataclass
from typing import List
from __init__ import CONFIG


@dataclass
class SearchHit:

    hit: dict
    display_fields: dict

    def get_field_value(self, field: str):
        """get the field value. field given in plain text"""
        res = deepcopy(self.hit["_source"])
        ajr = field.split(".")
        for s in ajr:
            if s in res:
                res = res[s]
            else:
                return None
        return res
    
    def has_field(self, field: str):
        return self.get_field_value(field) is not None
    
    def get_file_url(self) -> str:
        """Method to get the file URL for a hit. this is to be used in links"""
        url = self.get_field_value("file.url")
        if not url is None:
            url = url.replace("file://", "file:///")
        return url

    def hit_to_table(self):
        table_rows = []
        for display in self.display_fields:
            # read field value from dictionary
            field_value = self.get_field_value(display["field"])
            if field_value is None:
                continue
            # in case we need to use highlighted format, read the value from highlights
            if "use_highlights" in display and display["use_highlights"] and "highlight" in self.hit:
                field_value = "...".join(self.hit["highlight"][display["field"]])
            if "max_length" in display and len(field_value) > display["max_length"]:
                field_value = field_value[:display["max_length"]] + "..."
            # format field according to styling information
            formatted = display["style"].replace("$VALUE", field_value)
            # collect data to table
            table_rows.append((display["display_name"], formatted))
        return table_rows
    
    def hit_title(self):
        extention = str(self.get_field_value("file.extension")).upper()
        return "<a href=/view/{}/{} class=\"document-title\">{} file</a>".format(self.hit["_index"], self.hit["_id"], extention)

    def make_html(self) -> str:
        """Make required html for presenting the hit in the search resutls"""
        s = self.hit_title()
        table_rows = self.hit_to_table()
        # convert table to HTML
        s += "<table class=\"document-table\">"
        for name, value in table_rows:
            s += "<tr><td class=\"key\">{}</td><td class=\"value\">{}</td></tr>".format(name, value)
        s += "</table>"
        return s

def hits_from_resutls(results) -> List[SearchHit]:
    hits = results['hits']['hits']
    ajr = []
    for hit in hits:
        ajr.append(SearchHit(hit, CONFIG["display_fields"]))
    return ajr
