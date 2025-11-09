<h2>Elastic</h2>
Для предварительного заполнения ES был подготовлен snapshot. Для заполнения нужно выполнить две команды регистрация репозитория и копирование снэпшота. 
</br>
</br>
Регистрация репозитория:

```bash
curl -X PUT "http://localhost:9200/_snapshot/local_backup" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "fs",
    "settings": { "location": "/usr/share/elasticsearch/snapshots" }
  }'
```

Копирование:
```bash
curl -X POST "http://localhost:9200/_snapshot/local_backup/snapshot_1/_restore" -H 'Content-Type: application/json' -d '
{
  "indices": "api_index,params_index",
  "ignore_unavailable": true,
  "include_global_state": false
}'
```
Создание (на случай необходимости сохранить):
```bash
curl -X PUT "http://localhost:9200/_snapshot/local_backup/snapshot_1?wait_for_completion=true"
```