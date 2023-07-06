# verify_url="http://localhost:8000/trustList/DSC/"
# verify_url="https://de.dscg.ubirch.com/trustList/DSC"
verify_url = "http://localhost:8000/trustList/DSC/"  # URL bei der beim hochladen auf der webseite die keys zum prüfen geholt werden
localcert = True  # ob auf die lokalen public keys oder die offiziellen zugegriffen werden soll, also das was "/trustList/DSC" zur Verfügung gestellt werden soll
offlinemode = True  # ist der offline mode an, wird auf eine offline version der offiziellen backends zurückgegriffen
