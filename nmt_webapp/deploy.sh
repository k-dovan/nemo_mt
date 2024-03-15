# copy supervisor config file to the supervisor's default configuration location
cp nmt_service.conf /etc/supervisor/conf.d/
echo "Copied nmt_service.conf to supervisor's location."

# update the supervisor configs
supervisorctl update
echo "Updated nmt_service services."
