---
icon: link
description: >-
  This page details each host function and what it does. Each different module
  and group of functions are separated into their own section so you can quickly
  find what you need.
---

# Host functions

### Global Types

```
Color:
- r: int - Red
- g: int - Green
- b: int - Blue
- a: Optional[int] - An optional alpha, default to 255 if not passed
```

```
TextColors:
- foreground: Color - The text color
- background: Optional[Color] - An optional background to put behind the text, to help with visibility
```

```
ConfigGet[T]: - Make sure you parse the value correctly once you receive it
- value: T - The typed return value 
```

```
ConfigSet[T]: - Make sure you serialize the value correctly when sending it
- key: str - The key of the particular item to be set
- value: T - The typed value to set
```

```
MossState:
- width: int - The width and of the moss window
- height: int
- current_screen: str - The class name of the current moss screen
- opened_context_menus: List[str] - A list of class names of all opened context menus
- icons: List[str] - A list of all the icons loaded by moss
```

{% hint style="success" %}
Moss will not start loading extensions until all assets are loaded
{% endhint %}

{% hint style="warning" %}
Moss will only load extension specified assets after all extensions are loaded
{% endhint %}

## GUI functions

### GUI types

```markup
ContextButton:
- text: str - The text on the button
- icon: str - The icon to use for the button
- context_icon: Optional[str] - The bottom right icon used if your button is right clickable
- action: str - The extension function / callback to call when clicked
- context_menu: Optional[str] - The extension function to call to get the context menu when right clicked
```

```markup
ContextMenu:
- key: str - The key of your context menu
- buttons: List[ContextButton] - The buttons it should contain 
```

### Context menu functions

<pre class="language-python"><code class="lang-python"><strong>moss_gui_register_context_menu(menu: ContextMenu)
</strong></code></pre>

Creates a context menu within Moss that you can refer to. This function is usually meant to be called during extension registration.

```python
moss_gui_open_context_menu(key: str, x: int, y: int)
```

Activates any registered context menu onto your screen on the specified `x`and `y` coordinates. The context menu will remain open unless the user clicks outside of it.

### Miscellaneous functions

```python
moss_gui_invert_icon(key: str, result_key: str)
```

This function inverts any icon key you give it and will store the result into the respective result\_key. You can pass the same key both arguments to permanently invert that icon instead of making an inverted duplicate. You can use this to invert your own assets or to create something like the Moss dark mode extension.

## Defaults functions

Defaults refers to a class in Moss which globally describes every single configuration such as paths to folders or colors, these can be changed or viewed by extensions but whether or not Moss would respond to any changes depends highly on when you call any set function, it is recommended to do so at the registration stage!

### Functions for setting/getting colors

```python
moss_defaults_set_color(key: str, color: Color)
```

This function sets that particular color in the Defaults, ideal at registration.

```python
moss_defaults_get_color(key: str) -> Color
```

Likewise this function will return any particular color from the Defaults.

```python
moss_defaults_set_text_color(key: str, colors: TextColors)
```

This function sets that particular set of text colors in the Defaults, again ideal at registration, even though most UI will refresh texts depending on the situation.

```python
moss_defaults_get_text_color(key: str) -> TextColors
```

This function returns that particular set of text colors from the Defaults.

### Functions for setting/getting values

```python
moss_defaults_get(key: str) -> ConfigGet[T]
```

This function returns any value given the key in Defaults, it is passed to the extension as an object containing the typed value, your extension needs to properly parse the value's type.

```python
_moss_defaults_set(value: ConfigSet[T])
```

This function sets any value given the key in Defaults, it accepts the value as is from the extension and your extension needs to properly type it if it is updating an existing value. Your [SDK](getting-started.md#choosing-an-sdk) should abstract any type to be passed directly instead of `ConfigSet` .

## Extension manager functions (EM)

All these functions are closely related to either your interactions with Moss and the extension manager or accessing things available to your extensions / other extensions.

### Functions for setting/getting config values

Some of these are very similar to the defaults as they are related to setting the config file. You can take a look [above](host-functions.md#functions-for-setting-getting-values) for more information on these functions. Your extension is granted one config file it can use and it is automatically saved and managed for you.

```python
moss_em_config_get(key: str) -> ConfigGet[T]
```

<pre class="language-python"><code class="lang-python"><strong>_moss_em_config_set(value: ConfigSet[T])
</strong></code></pre>

### Functions for managing your extension

You can find more info on ContextButton [above](host-functions.md#types)

```python
moss_em_register_extension_button(button: ContextButton)
```

This function registers one or more context buttons to be passed to the side menu "Extensions" context menu. It is recommended that if you choose to add a button you'd only add one and then that would open a context menu or a screen that can there allow the user to further interact with your extension.

### Functions of the extension manager

```python
moss_em_export_statistical_data()
```

This function exports the extension manager's statistical call data to `TEMP_DIR/extension_calls.json` , the data is stored in the following format:

`dictionary -> extension_name : dictionary -> function_name : call count`&#x20;

{% hint style="warning" %}
Statistics have to be enabled by the user for Moss to setup the proper statistic tools
{% endhint %}

```python
moss_em_get_state() -> MossState
```

This function is useful if you need the state of Moss but are running code outside the loop function which would otherwise receive the state automatically.

## Pygame extra functions (PE)

### Pygame extra types

```
PygameExtraRectEdgeRounding:
- edge_rounding: Optional[int] - Sets all the below, -1 / None for disable
- edge_rounding_topright: Optional[int]
- edge_rounding_topleft: Optional[int]
- edge_rounding_bottomright: Optional[int]
- edge_rounding_bottomleft: Optional[int]
```

```
Rect:
- x: int - The left of the rect
- y: int - The top of the rect
- width: int - The width of the rect
- height: int - The height of the rect
```

```
PygameExtraRect:
- color: Color - The color of the rect
- rect: Rect - The rect of the rect lol
- width: int - The width of the rect's outline, or 0 for filled
- edge_rounding: Optional[PygameExtraRectEdgeRounding] - Optional rounding of the
```

```
Screen & ChildScreen: - These are considered UI rendering objects and will have respective context handling
- key: str - An identifier for the screen
- screen_pre_loop: Optional[str] - An extension function for the before loop call
- screen_loop: str - An extension function for the loop call
- screen_post_loop: Optional[str] - An extension function for the after loop call
- event_hook: Optional[str] - An extension function which will receive API events, must accept a single argument name: String
```

{% hint style="info" %}
Notice that everything except the key and loop are optional functions you can use and are not required to be passed!
{% endhint %}

### Functions for drawing basic shapes

```python
_moss_pe_draw_rect(draw: PygameExtraRect)
```

This function draws a basic rectangle. Your [SDK](getting-started.md#choosing-an-sdk) should abstract this, typically to expand the individual components of `PygameExtraRect` into arguments instead.

### Custom screens

The first steps for making custom screens with Moss is registering your extension's functions with a custom screen, so Moss can create your screen and call your extension

```python
moss_pe_register_screen(screen: Screen)
```

This function will register your screen with Moss, you can also use to register children screens, which are screens to be rendered on top of other screens (things like popups, context menus for example, but Moss already has those for you)

```python
_moss_pe_open_screen(key: str, initial_values: dict) -> int
```

This function will open a new instance of your screen in Moss. Your [SDK](getting-started.md#choosing-an-sdk) should manage the initial\_values to be serialized before passing through extism. It returns the id of the screen in Moss.

```python
moss_pe_get_screen_value(key: str) -> ConfigGet[T]
```

This function will get any value from the screen that you passed through using initial\_values or set separately. This function can optionally fetch variables or properties on the screen, as long as they are serializable.

```python
_moss_pe_set_screen_value(value: ConfigSet[T])
```

This function will update any value from the screen that you passed through using initial\_values or set any extra values.

## Text

Moss has an approach to text where you can create a text and Moss returns an id, from there you can call functions on this text through many small functions. Your [SDK](getting-started.md#choosing-an-sdk) should implement this in an OOP way that allows the user to store and manipulate text objects easily on the extension while forwarding all changes to Moss.

### Functions for managing text

```python
moss_text_make(text: str, font: str, font_size: int, colors: TextColors) -> ConfigGet[int]
```

Creates a text and gives you the ID that you can use to refer to this text object. Please note that the font here refers to the font path.

Any further functions where you see `text_id: int` it is referring you to pass the ID you got from `moss_text_make` .

```python
moss_text_set_text(text_id: int, text: str) -> Rect
```

This updates the text object and renders new text, this operation shouldn't be done extensively unless your text needs to change often, text objects are optimized to not be updated often and just displayed.

```python
moss_text_set_font(text_id: int, font: str, font_size: int) -> Rect
```

This updates both the font file, given a path and the font size, it will also regenerate the text object for you and position it in the center of wherever it was before.

{% hint style="info" %}
Notice that the above functions return the text rect, this is important and it is due to the fact that the rect of the text would have changed. It simplifies calls
{% endhint %}

```python
moss_text_set_rect(text_id: int, rect: Rect)
```

Updates the text rect, this determines the text position.

```python
moss_text_get_rect(text_id: int) -> Rect
```

Gets the text rect, the reason it's a rect is to provide the text size. The [SDK](getting-started.md#choosing-an-sdk) you use should probably run this after making a text in order to have all the values of the text locally in your extension

### Displaying text

```python
moss_text_display(text_id: int)
```

There's not much special about this function, it will display the text at the topleft of the rect, the size of the rect is determined by the text size so the text should be effectively be drawn within this are. Please note that the text background you passed is automatically drawn too as part of this operation.

## Basic API usage

### API Models

```
RM_File:
- content_count: int - The amount of sub data included in the file
- hash: str - The file hash
- rm_filename: str - A reference to the rm_filename Header for this file
- size: int - The total byte size of all sub data(s) / data combined
- uuid: str - The uuid of the file (This can include the file extension typically)
```

```
RM_TimestampedValue[T]:
- timestamp: str - A string formatted datetime
- value: Optional[T] - The stored typed value
```

```
RM_Tag:
- name: str - The name of the tag
- timestamp: int - The last time it was added
```

```
RM_Page:
- id: str
- index: RM_TimestampedValue
- template: RM_TimestampedValue
- redirect: Optional[RM_TimestampedValue]
- scroll_time: Optional[RM_TimestampedValue]
- vertical_scroll: Optional[RM_TimestampedValue]
```

```
RM_CPagesUUID:
- first: str - Author uuid
- second: int - Index?
```

```
RM_CPages:
- pages: List[RM_Page]
- original: RM_TimestampedValue
- last_opened: RM_TimestampedValue
- uuids: List[RM_CPagesUUID] - The uuids of the authors
```

```
RM_Zoom: # RAW
- zoomMode: ZoomModes
- customZoomCenterX: int
- customZoomCenterY: int
- customZoomPageHeight: int
- customZoomPageWidth: int
- customZoomScale: float
```

```
RM_Content:
- hash: str - The hash of the content file
- c_pages: RM_CPages - The full page information
- cover_page_number: int - Either 0 or -1, aka last page or first page
- file_type: FileTypes - The type of document, like notebook or epub...
- version: int - Should be 2, Moss will always convert version 1 to 2
- usable: bool - Used by moss to signify if it was able to fully parse the content
- zoom: RM_Zoom - The zoom preference on the document
- orientation: Orientations - The document's orientations
- tags: List[RM_Tag] - A list of the tags on the document
- size_in_bytes: int - The length in bytes of all the content data files combined
- dummy_document: bool - IDK ask reMarkable
```

```
RM_Metadata:
- hash: str - The hash of the metadata file
- type: DocumentTypes - If it is a document or a collection
- parent: Optional[str] - if None then the parent is `My files` or "trash" otherwise uuid of collection
- created_time: int
- last_modified: int
- visible_name: str
- metadata_modified: bool
- modified: bool - IDK ask reMarkable
- synced: bool - IDK ask reMarkable
- version: Optional[int]
# The metadata of documents includes this additional information
- last_opened: int - A timestamp of the last time the document was opened
- last_opened_page: int - The index of the last page opened
```

```
RM_DocumentCollection:
- tags: List[RM_Tag] - The list of tags on the collection
- metadata: RM_Metadata - The metadata for the collection
- uuid: str - The uuid of the collection, set parent to this to move a document
- has_items: bool - A variable provided by rmapi to indicate if it scanned any documents with this collection as the parent
```

```
RM_Document:
- files: List[RM_File] - All the files on this document
- content: RM_Content - The content information
- metadata: RM_Metadata - The document metadata
- uuid: str - The uuid of the document
- server_hash: Optional[str] - The hash of this file as it was last on the server (for checking changes)
- files_available: List[str] - A list of uuid(s) of the files that have been checked
- downloading: bool - If Moss has an operation to download data
- provision: bool - Used by Moss to signify if the document is staged for uploading
- available: bool - A property that shows if all the files are in the available files
```

```
RM_RootInfo:
- generation: int - A number for reference (IDK ask reMarkable)
- hash: str - The hash of the file that is root / to be root
```

{% hint style="warning" %}
The above are made for connectivity of the extensions, some data is only used by Moss!Changing some things may not result in permanent changes, especially if the value is not a reMarkable value to begin with, or if you forgot to upload to the cloud!
{% endhint %}

Additionally here are some of the enums that you may have noticed above.

```
ZoomModes:
- 'bestFit' - Default
- 'customFit'
- 'fitToWidth'
- 'fitToHeight'
```

```
FileTypes:
- 'pdf'
- 'epub'
- 'notebook'
```

```
Orientations:
- 'portrait'
- 'landscape'
```

```
DocumentTypes:
- 'DocumentType'
- 'CollectionType'
```

### Data models

These models are referenced below when creating new instance of API objects

{% hint style="warning" %}
Your extension is allowed to pass data only using file paths! This can either be downloaded content like pdfs, rm files or epub, but must be passed in as a path for Moss to read in and save RAM.
{% endhint %}

```
DocumentNewNotebook:
- name: str - This is the visible name
- parent: Optional[str] - Null is `My Files` and so on...
- document_uuid: Optional[str]
- page_count: int - Just pass 1 for default
- notebook_data: List[str] - A list of paths to .rm files
- metadata_id: Optional[str]
- content_id: Optional[str]
```

```
DocumentNewPDF:
- name: str
- pdf_data: str - The path to the PDF
- parent: Optional[str]
- document_uuid: Optional[str]
```

```
DocumentNewEPUB:
- name: str
- epub_data: str - The path to the EPUB
- parent: Optional[str]
- document_uuid: Optional[str]
```

{% hint style="success" %}
Not passing a document\_uuid will use a randomly generated uuid which you'll receive from the function. See below.
{% endhint %}

### Important information for SDK usage

There's a lot of functions here that you can work with, your [SDK](getting-started.md#choosing-an-sdk) should implement these in a OOP way.\
here they will be listed in rapid succession, you'll see that most of them share similar patterns, the data they access is relevant to the function name so it should be obvious what each function does.

{% hint style="success" %}
A note for SDK developers, your RM\_Metadata / RM\_Content objects will receive accessor reference. This is either `document_uuid` or `collection_uuid`. The purpose of these are to help you with which set of functions to use for **set**/**get** operations, but ideally you could just use **set** since most document data won't change.
{% endhint %}

### Managing document data

```python
moss_api_document_get(document_uuid: str, key: str) -> ConfigGet[T]
_moss_api_document_set(document_uuid: str, value: ConfigSet[T])
moss_api_document_get_all(document_uuid: str) -> RM_Document
```

### Managing document sub data

#### Metadata

```python
moss_api_document_metadata_get(document_uuid: str, key: str) -> ConfigGet[T]
_moss_api_document_metadata_set(document_uuid: str, value: ConfigSet[T])
moss_api_document_metadata_get_all(document_uuid: str) -> RM_Metadata
```

#### Content

```python
moss_api_document_content_get(document_uuid: str, key: str) -> ConfigGet[T]
_moss_api_document_content_set(document_uuid: str, value: ConfigSet[T])
moss_api_document_content_get_all(document_uuid: str) -> RM_Content
```

### Managing collection data

```python
moss_api_collection_get(collection_uuid: str, key: str) -> ConfigGet[T]
_moss_api_collection_set(collection_uuid: str, value: ConfigSet[T])
moss_api_collection_get_all(collection_uuid: str) -> RM_DocumentCollection
```

### Managing collection sub data

```python
moss_api_collection_metadata_get(collection_uuid: str, key: str) -> ConfigGet[T]
_moss_api_collection_metadata_set(collection_uuid: str, value: ConfigSet[T])
moss_api_collection_metadata_get_all(collection_uuid: str) -> RM_MetadataBase
```

### Managing metadata and content standalone objects

{% hint style="success" %}
All standalone metadata and content objects are stored by the extension manager, these objects are referenced by id which is an integer. \
The accessor references are: `metadata_id` and `content_id`
{% endhint %}

#### Metadata

Here are the functions for creating standalone metadata objects

...

Here are the functions for managing the fields

```python
moss_api_metadata_get(metadata_id: int, key: str) -> ConfigGet[T]
_moss_api_metadata_set(metadata_id: int, value: ConfigSet[T])
moss_api_metadata_get_all(metadata_id: int) -> RM_MetadataDocument
```

#### Content

Here are the functions for creating standalone content objects

...

Here are the functions for managing the fields

```python
moss_api_content_get(content_id: int, key: str) -> ConfigGet[T]
_moss_api_content_set(content_id: int, value: ConfigSet[T])
moss_api_content_get_all(content_id: int) -> TRM_Content
```

### Functions for documents

All the functions here are related to either creating or managing documents

#### Creating documents

{% hint style="info" %}
Each creating function below returns the new document's UUID.
{% endhint %}

{% hint style="warning" %}
Refer to your [SDK](getting-started.md#choosing-an-sdk) for specific implementations. Typically since most fields are not required, the SDK should use a builder with defaults for the fields that aren't needed.
{% endhint %}

```python
moss_api_document_new_notebook(value: DocumentNewNotebook) -> str
moss_api_document_new_pdf(value: DocumentNewPDF) -> str
moss_api_document_new_epub(value: DocumentNewEPUB) -> str
```

#### Managing documents

```python
moss_api_document_duplicate(document_uuid: str) -> str
```

Returns the UUID of the new duplicate. This function randomizes a lot of the UUIDs of the document, it will also update timestamps and set the document to provision.

```python
moss_api_document_randomize_uuids(document_uuid: str) -> str
```

This function is self explanatory, it will modify all the document UUIDs including nested UUID references to a new random UUID and return the new UUID.

```python
moss_api_document_unload_files(document_uuid: str)
```

Simply unloads any files that Moss has loaded on the document. Documents will usually be automatically unloaded upon closing. If your extension loaded files though, this is the way to unload them and you should!

```python
moss_api_document_load_files_from_cache(document_uuid: str)
```

This function loads all the files enforcing cache usage only. If the cache misses a file, it will not be downloaded.

```python
moss_api_document_ensure_download_and_callback(document_uuid: str, callback: str)
```

Document downloads are threaded, this is one way to check for when your document has finished downloading. The callback as all other extension functions accepts the name of your extension callback function.

```python
moss_api_document_ensure_download(document_uuid: str)
```

This function is very similar to the above, but it does not run a callback when the document is finished downloading.

```python
moss_api_document_export(document_uuid: str)
```

This function prepares the document for uploading to the cloud. It prepares data and hashes converting the metadata and content data into raw data for upload.
