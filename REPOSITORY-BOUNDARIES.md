# Repository boundaries

| Location | Role | Contents |
|---|---|---|
| `/Users/shayan/Projects/SpielOS1` | Reusable product source | Core code, generic install/host templates, packaging, synthetic fixtures |
| `/Users/shayan/Projects/SpielOS-Website` | Local personal company home | Director, installed Departments, Skills, workflows, private data, production sources and artifacts |
| `/Users/shayan/ShayanSpiel.Github.io` | Public website | Pages, components, design tokens, public snapshots and approved released media |

Product source is published at `ShayanSpiel/SpielOS`; the website has its own
`ShayanSpiel/ShayanSpiel.Github.io` remote. The local company home is an
installation, has no Git remote, and must not be pushed as public source. Its
current Projects location replaces the obsolete Desktop location.

Company work starts from that home. Its `tools/spielos-local` launcher selects
the home regardless of the current folder. Its `tools/update-spielos` command
fast-forwards the source and refreshes shipped runtime/host files while
retaining all existing files, personal content, and data.

Website builds consume only committed public metadata and released media.
They never import private company files or follow links into another repo.
Production workflows consume explicit local snapshots of the public design
system. Existing misplaced material was previously relocated and hash
recorded in the home; this cleanup records those completed relocations in
Git. Never delete existing files or create new backups.

Website publishing follows the website's existing deployment workflow.
Repository pushes and public releases require explicit owner authorization.
