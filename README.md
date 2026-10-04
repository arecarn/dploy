# Dploy

Dploy is a tool for creating symbolic links similarly to [GNU
Stow](https://www.gnu.org/software/stow/). It is provided as a CLI tool and
Python 3.10+ module and supports Windows, Linux, and OSX.

Dploy's command `stow` creates symbolic links to the contents of packages in a
specified destination directory. Repeating the
`stow` command with the same arguments will confirm that the contents of the
package have been symbolically linked.

Dploy's command `unstow` removes symbolic links that resulted from `stow`
commands. Repeating the `unstow` command with the same arguments will confirm
that the links to stowed packages have been removed.

## Installation

* Latest Release: `pip install dploy`
* Development Version: `pip install git+https://github.com/arecarn/dploy.git`

## Basic CLI Usage

* `dploy stow <package-directory>... <destination-directory>`
* `dploy unstow <package-directory>... <destination-directory>`
* `dploy clean <package-directory>... <destination-directory>`
* `dploy --help`

## Rationale

Dploy started out as simple Python script to create symbolic links to my
dotfiles for Windows, Mac, and Linux. Over time I keep improving and tweaking my
script to suit my needs, but I was running into a problem.  Keeping all the
files I wanted to link in a config file was becoming a real pain in the neck.

I started looking for another solution to solve my problem, and found many
alternatives but none of them seemed to be a good fit. The solution that seemed
the most promising was using GNU Stow. It seemed like the most simple elegant
solution to the problem. The only issue was that it didn't support Windows.

Then I thought to myself, why can't I just create my own version of Stow that
work on Windows, Linux and OSX. So after that my I started morphing
simple python script into what would become Dploy and learned a lot more about
python in the process.

## How does it compare with GNU Stow?

Below are just a few few major points of comparison between GNU stow and Dploy.

* Like GNU Stow Dploy runs in two passes. First by collecting the actions
  required to complete the command and verifying that the command can
  completed without any issues. If no issues are detected then the second
  pass executes these actions are execute to complete the command. Otherwise
  Dploy will exit and indicate why the command can not be completed. This way a
  stow or unstow operation is atomic and never partially done.

* Like Stow, Dploy supports tree folding and tree unfolding. Like Stow's
  `--no-folding`, passing `--no-folding` to `stow` or `unstow` disables
  folding, so each file gets its own link inside a real directory.

* Unlike Stow, Dploy requires an explicit package(s) and a destination
  directory.

* Unlike Stow, Dploy does not have any concept of ownership, but will only
  operate on symbolic links and the creation or removal of directories for these
  symbolic links.

* Unlike Stow, Dploy's `unstow` removes a destination directory that becomes
  empty as a result of removing its symbolic links, even if that directory
  existed before `stow` created any links inside it. Dploy keeps no state
  across invocations, so it cannot distinguish a directory it created from
  one that already existed.

* `stow`'s `--skip-conflicts` flag is the one opt-in exception to the
  atomicity described above: files that conflict with an existing,
  unmanaged destination entry are skipped and reported, while every other
  file in the package is still linked. `dploy` exits with status `2` when
  this happens, so a script can tell a partial stow apart from a full
  success (status `0`) or a fatal error (status `1`).
