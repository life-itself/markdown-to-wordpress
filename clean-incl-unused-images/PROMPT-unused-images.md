Make a list of all image files in content directory and then find out which markdown or jsx/html files they are used in (so that we can work out which images are unused).

You should search just by basename of the image file (not full path).

## Outputs

- [ ] Text file with a list of images
- [ ] csv file of usage as per description below
- [ ] Python file for doing this work

### csv file headings

```
image | used | files
```

- `image` is path to image
- used is `y/n` indicated if image is used somewhere
- files is list of files separated by ` :: ` where image is used
