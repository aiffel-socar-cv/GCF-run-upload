# GCF-run-upload

## How to run this code

1. Connect to the Cloud PSQL

```SQL
gcloud sql connect viai-images --user=postgres --quiet
```

2. Upload new image to the `images-original` bucket with the sample images

```SQL
gsutil cp sample_images/input/img_0253.png gs://images-original/originals
```

3. Check the logs

```SQL
gcloud functions logs read --limit 50
```

4. Check the SQL

```SQL
select * from entries;
```

Sample result)

![sample result](./result.png)
