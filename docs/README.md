# hdmi Documentation

This directory contains the documentation for the hdmi project, built using [Sphinx](https://www.sphinx-doc.org/) and organized according to the [Diátaxis framework](https://diataxis.fr/).

## Documentation Structure

The documentation is organized into four categories based on the Diátaxis framework:

### 📚 Tutorials (`tutorials/`)
**Learning-oriented**: Help newcomers learn by doing

- Step-by-step instructions
- Complete working examples
- Assumes little prior knowledge
- Example: "Getting started with hdmi"

### 🛠️ How-To Guides (`how-to/`)
**Goal-oriented**: Solve specific problems

- Focused on accomplishing specific tasks
- Assumes basic knowledge
- Practical and actionable
- Example: "How to use service definitions with factories"

### 📖 Reference (`reference/`)
**Information-oriented**: Technical descriptions

- API documentation
- Complete and accurate technical details
- Generated from docstrings where appropriate
- Example: "Container API reference"

### 💡 Explanation (`explanation/`)
**Understanding-oriented**: Background and context

- Architecture and design decisions
- Conceptual background
- Why things are the way they are
- Example: "Why late-binding dependency resolution"

## Building the Documentation

### Prerequisites

Install development dependencies:

```bash
uv sync --all-extras
```

### Build Commands

```bash
# Build HTML documentation
make docs

# Build and watch for changes (auto-reload in browser)
make docs-watch

# Clean build artifacts (includes docs)
make clean
```

The built documentation will be in `docs/_build/html/`. Open `docs/_build/html/index.html` in your browser to view it.

## Writing Documentation

### Adding New Documentation

1. Determine which Diátaxis category your content belongs to
2. Create a new `.rst` file in the appropriate directory
3. Add it to the `toctree` in that category's `index.rst`
4. Build and review your changes

### reStructuredText Syntax

Sphinx uses reStructuredText (RST). Here are some common patterns:

```rst
Section Header
==============

Subsection
----------

**bold text**
*italic text*
``code text``

.. code-block:: python

   # Code example
   def example():
       pass

.. note::
   This is a note admonition.
```

For more information, see the [Sphinx documentation](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html).

## Contributing

When adding new features:

1. Update the **Reference** section with API documentation
2. Add **How-To Guides** for common use cases
3. Update **Explanation** for architectural decisions
4. Create **Tutorials** for end-to-end learning paths

Remember: Documentation is as important as code. Every feature should be documented following TDD principles - write the documentation as you write the tests and implementation.
