import json
import re
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

# All official South Australian councils
SA_COUNCILS = [
    "Adelaide Hills Council", "Adelaide Plains Council", "Alexandrina Council",
    "Barossa Council", "Barunga West Council", "Berri Barmera Council",
    "Campbelltown City Council", "City of Adelaide", "City of Burnside",
    "City of Charles Sturt", "City of Holdfast Bay", "City of Marion",
    "City of Mitcham", "City of Norwood Payneham and St Peters",
    "City of Norwood Payneham & St Peters", "City of Onkaparinga",
    "City of Playford", "City of Port Adelaide Enfield", "City of Port Lincoln",
    "City of Prospect", "City of Salisbury", "City of Tea Tree Gully",
    "City of Unley", "City of Victor Harbor", "City of West Torrens",
    "City of Whyalla", "Clare and Gilbert Valleys Council", "Cleve District Council",
    "Coorong District Council", "Copper
