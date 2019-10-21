# Abstract Shrewd Owned Models

This is the central repo for our course on building reusable apps with Django.

First, this course is agile.

That is, I mean, while we have a holistic idea of what we're to achieve at the end of the day, we have not planned out every detail of it.

And because this course is self-organizing, we'll be adopting the Test Driven Development (TDD) approach in order to ensure that at any instant in time we're responding only to a unit change in the requirement - and that we fix every resulting (exposed) regression.


## What's the _holistic_ idea, anyways?

We'll be building a package for adding some sort of shrewd behaviour to our Django models. We've written such behaviours (in different forms) into a good number of models in our previous projects. But that's really not DRY.

So, we've recognised the pattern, and are going to abstract it away into a reusable package which we'll host on PyPI.


## Learning Points

We'll be diving into the internal workings of querysets and models managers, and how they come to play with models.

We'll encounter the nuances of testing abstract models, effectively exposing ourselves to some of the _magic_ which goes on in the background when Django builds models out of the code we write.

On the non-django side of things, we'll gain experience in hosting Python packages on PyPI.

And, oh, we'll be using the Github Flow approach to branching, so everyone will know how to contribute to Open Source projects in the future.
