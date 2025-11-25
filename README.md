Migrating markdown to wordpress for LifeItself.org

## Analysis

### Node vs Python

**Let's go with NodeJS for now**

Facts first:

* The WordPress REST API is language-agnostic; anything that can do HTTP+JSON works. ([WordPress Developer Resources][1])
* The “first-class” client ecosystem is still strongest on the JavaScript side:
  * Core ships with a JS client (Backbone-based wp-api) for REST. ([WordPress Developer Resources][2])
  * There is a well-maintained Node client `node-wpapi`, and newer typed JS clients such as `wordpress-api-client`. ([wp-api.org][3])
* Python also has decent wrappers (e.g. `wp-api-python`, `wp-api-client`, `wordpress-api-client`) built on `requests`. ([GitHub][4])

Given your existing JS/Markdown tooling and the slightly richer JS ecosystem around WordPress, I would lean to:

* Default: Node.js (TypeScript if you like typing), with `node-wpapi` or a thin `fetch` wrapper. ([wp-api.org][3])
* Use Python if you want tighter integration with other Python data tooling; the modern `wp-api-client` looks quite capable. ([wp-api-client.readthedocs.io][5])

Either way, the high-level spec is identical; only library details change.

### Markdown in Wordpress

**Not possible. there is no way to upload markdown into a block in wordpress and have it rendered.*

**=> we'll need to convert from markdown on the way in ...**

* Gutenberg does not natively “store” Markdown as Markdown; it converts typed Markdown syntax into blocks/HTML. ([WordPress.org][6])
* Markdown blocks exist via plugins (Jetpack Markdown block, “Markdown Block”, etc.), but these still render to HTML/block markup internally; they are not a general “store raw .md and keep it forever” mechanism. ([Jetpack][7])
