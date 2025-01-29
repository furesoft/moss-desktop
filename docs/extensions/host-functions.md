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

## GUI functions

### Types

```markup
ContextButton:
- text: str - The text on the button
- icon: str - The icon to use for the button
- context_icon: str - The bottom right icon used if your button is right clickable
- action: str - The extension function / callback to call when clicked
- context_menu: str - The extension function to call to get the context menu when right clicked
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

## Pygame extra functions (PE)

### Types

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
_moss_pe_open_screen(key: str, initial_values: dict)
```

This function will open a new instance of your screen in Moss. Your [SDK](getting-started.md#choosing-an-sdk) should manage the initial\_values to be serialized before passing through extism

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
