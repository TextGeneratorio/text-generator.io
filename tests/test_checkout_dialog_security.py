import subprocess
import textwrap
from pathlib import Path


def test_checkout_dialog_does_not_initialize_live_stripe_on_http_origin():
    script_path = Path("static/js/checkout-dialog.js").resolve()
    node_script = textwrap.dedent(
        f"""
        const fs = require('node:fs');
        const vm = require('node:vm');
        const source = fs.readFileSync({str(script_path)!r}, 'utf8');

        function makeSandbox(url) {{
            const elements = {{}};
            const calls = {{ stripe: 0, fetch: 0 }};
            const windowUrl = new URL(url);
            const document = {{
                readyState: 'loading',
                head: {{
                    appendChild: () => {{
                        throw new Error('Stripe script should not be appended on HTTP');
                    }}
                }},
                body: {{
                    style: {{}},
                    insertAdjacentHTML: () => {{
                        elements['checkout-dialog'] = {{
                            style: {{}},
                            classList: {{ add: () => {{}}, remove: () => {{}} }}
                        }};
                        elements['checkout-container'] = {{ innerHTML: '' }};
                    }}
                }},
                addEventListener: () => {{}},
                createElement: () => ({{ addEventListener: () => {{}} }}),
                getElementById: (id) => elements[id] || null,
                querySelector: () => null
            }};
            const sandbox = {{
                console,
                document,
                module: {{ exports: {{}} }},
                setTimeout,
                URL,
                window: {{
                    STRIPE_PUBLISHABLE_KEY: 'pk_live_test',
                    location: {{
                        protocol: windowUrl.protocol,
                        hostname: windowUrl.hostname,
                        pathname: windowUrl.pathname,
                        search: windowUrl.search,
                        hash: windowUrl.hash
                    }},
                    prompt: () => '100'
                }},
                fetch: async () => {{
                    calls.fetch += 1;
                    return {{ ok: false }};
                }},
                Stripe: () => {{
                    calls.stripe += 1;
                    throw new Error('Stripe should not be initialized on HTTP');
                }}
            }};
            sandbox.window.fetch = sandbox.fetch;
            sandbox.window.console = console;
            vm.createContext(sandbox);
            vm.runInContext(source, sandbox);
            return {{ sandbox, calls, elements }};
        }}

        (async () => {{
            const {{ sandbox, calls, elements }} = makeSandbox('http://93.127.141.100:8083/');
            const dialog = new sandbox.module.exports.CheckoutDialog();

            if (calls.stripe !== 0) {{
                throw new Error(`Stripe initialized during construction: ${{calls.stripe}}`);
            }}

            await dialog.show();

            if (calls.stripe !== 0) {{
                throw new Error(`Stripe initialized on insecure origin: ${{calls.stripe}}`);
            }}
            if (calls.fetch !== 0) {{
                throw new Error(`Checkout fetched user/session before HTTPS guard: ${{calls.fetch}}`);
            }}
            if (!elements['checkout-container'].innerHTML.includes('Secure checkout is only available')) {{
                throw new Error(`Missing secure checkout error: ${{elements['checkout-container'].innerHTML}}`);
            }}
        }})().catch((error) => {{
            console.error(error);
            process.exit(1);
        }});
        """
    )

    subprocess.run(["node", "-e", node_script], check=True)


def test_base_template_uses_versioned_site_local_checkout_dialog():
    template = Path("static/templates/base.jinja2").read_text(encoding="utf-8")

    assert '<script src="/static/js/checkout-dialog.js?v=5"></script>' in template
    assert '<script src="{{ static_url }}/js/checkout-dialog.js"></script>' not in template
    assert '<script src="https://js.stripe.com/v3/"></script>' not in template
