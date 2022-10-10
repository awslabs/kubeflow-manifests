---
date: 2022-10-10
title: "Announcing Kubeflow on AW"
linkTitle: "Announcing Kubeflow on AWS"
description: "Announcing Kubeflow on AWS"
author: Nadege Pepin ([@nadpepin](https://twitter.com/nadpepin))
resources:
- src: "**.{png,jpg}"
  title: "Image #:counter"
  params:
    byline: "Kubeflow on AWS"
---

**This is a test blog post**

The front matter specifies the date of the blog post, its title, a short description that will be displayed on the blog landing page, and its author.

## Including images

Here's an image (`featured-background.png`) that includes a byline and a caption.

{{< imgproc background Fill "600x300" >}}
Fetch and scale an image in the upcoming Hugo 0.43.
{{< /imgproc >}}

The front matter of this post specifies properties to be assigned to all image resources:

```
resources:
- src: "**.{png,jpg}"
  title: "Image #:counter"
  params:
    byline: "Photo: Riona MacNamara / CC-BY-CA"
```

To include the image in a page, specify its details like this:

```
{{< imgproc background Fill "600x300" >}}
Fetch and scale an image in the upcoming Hugo 0.43.
{{< /imgproc >}}
```

The image will be rendered at the size and byline specified in the front matter.


