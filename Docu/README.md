# DBMS_10 – Project Proposal for the Term Project

**Module:** Introduction to Database Management Systems · THGA Bochum
**Lecturer:** Stephan Bökelmann · <sboekelmann@ep1.rub.de>
**Prerequisites:** Lectures 01–10, exercises DBMS_01–DBMS_09

This exercise is **structured differently** from the previous ones: you do not
write code, you **design** your own database-backed system and submit a
**project proposal** to the lecturer. The proposal is the basis of your **term
project** (graded deliverable), in which you build a complete system over up to
two months (≈ 40 h of real work, including documentation and video).

**Architecture** — everything on the lecture server:

```
Frontend (installed .deb)  --HTTP + X-API-Key-->  FastAPI  -->  PostgreSQL
                                     backend orchestrated by Docker Compose
```

- **Backend** (PostgreSQL + FastAPI) runs in containers via Docker Compose.
- **Frontend** is built as a Debian installer (`.deb`) and installed next to it.
- Write endpoints are protected with an `X-API-Key`.

The term project is submitted as three parts: the **running system**, a
**documentation** (a GitHub repo with LaTeX CI + Makefile), and an **8–10 min
video** (`.mpg` to Moodle *or* an unlisted YouTube link).

## Repository layout

```
src/dbms_10.tex             # the exercise / assignment
proposal-template/          # fill-in skeleton students copy for the proposal
  proposal.tex
example-documentation/      # worked example of the final documentation
  documentation.tex
style/thga-db.sty           # THGA corporate design (copied from the course repo)
.github/workflows/build.yml # LaTeX build + release — copy this into your own repo
Makefile                    # builds all three PDFs into out/
out/                        # generated PDFs (not committed)
```

The `proposal-template/` and `example-documentation/` folders are meant to be
**copied**: start your proposal from the template, and model your documentation
repository on the example — together with the `Makefile` and
`.github/workflows/build.yml`, which build the PDF and publish it as a GitHub
Release on every tag push.

## Build

Requirement: `latexmk` and TeX Live (`apt install latexmk texlive-full`).

```bash
make          # builds out/dbms_10.pdf, out/proposal.pdf, out/documentation.pdf
make clean    # remove auxiliary files, keep PDFs
make distclean# remove everything including out/
```

## Releases

Pushing a tag matching `v*` triggers the GitHub Actions workflow, which builds
all three PDFs and attaches them to a GitHub Release automatically.
