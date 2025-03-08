# Moss desktop app

[![runs_on](https://img.shields.io/badge/runs_on-Extism-4c30fc.svg?subject=runs_on&status=Extism&color=4c30fc)](https://extism.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/RedTTGMoss/moss-desktop/total)
![GitHub Repo stars](https://img.shields.io/github/stars/RedTTGMoss/moss-desktop)

An open-source app for working with your documents in the reMarkable cloud

## Installation

You'll find builds under releases. The executable contains the app and an installer.

## Usage notes
Using this app to access your reMarkable cloud may cause reMarkable to take action on your account. So use this app at your own discretion! 

The app supports the api completely!

For information on how you can use moss check out the [docs](https://redttg.gitbook.io/moss/)

## Extensions
*Extensions are not supported not loaded by default.*

1. Run melora.py to start moss with extension injector melora

2. Upon first launch any extensions will be added to config

4. Enable the extensions you want in config.json file

5. Reload melora, a menu on the top right to access is available

Moss uses [extism](https://extism.org/) to support user extensions. 
There are several examples available:
[.Net](https://github.com/RedTTGMoss/Moss.NET.SDK)
[Darkmode with Rust](https://github.com/RedTTGMoss/extension_dark_mode)
[Rust Sdk Tester](https://github.com/RedTTGMoss/rust_sdk_tester)
[Moonbit](https://github.com/furesoft/moos-sdk-tester)

A brief instruction how to write your own extensions in the language of your choice can be found at the [docs](https://redttg.gitbook.io/moss/extensions/getting-started).

Here are some planned extensions We will create!

- Replace PDF function (the origin of this whole project)
- PDF Templates Store (with update support) **PLANNED NATIVE SUPPORT**
- nyaa.si ebook/pdf download
- Image(s) to PDF import
- Add Image to PDF function (from suggestion)
- Extension Store (A hub of verified extensions)
- Archiving (Automaticly archive documents based on certain conditions like a tag or date)
- Aggregated rss news feed
- Wikipedia crawler

## Contribution
This section describes the steps for contributors to best setup their work environment

**Your feature must be compatible with python 3.9**

1. Run the moss.py file
2. In the app input your cloud code
3. Wait for the initial sync
4. Please note that if you are developing changes to the cache system, all cached files are stored in sync folder
5. Make changes and test a new feature
The look and feel of this feature has to be paper-like
- Use the config.json, you can set `debug` to `true` in there! 
6. Make your pull request.
A few things will be checked
- Different screen resolution support
- API compatibility
