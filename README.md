<!-- markdownlint-disable MD033 MD036 MD041 MD045 MD046 -->

![Repo Banner](https://i.imgur.com/aJVikYa.png)

<div align="center">

<h1 style="border-bottom: none">
    <b><a href="#">Platzi Downloader</a></b>
</h1>

Es una herramienta de línea de comandos para descargar cursos directamente desde la terminal. Utiliza  ***`Python`*** y ***`Playwright`*** para automatizar el proceso de descarga y proporciona una interfaz de usuario amigable.

![GitHub repo size](https://img.shields.io/github/repo-size/ivansaul/platzi-downloader)
![GitHub stars](https://img.shields.io/github/stars/ivansaul/platzi-downloader)
![GitHub forks](https://img.shields.io/github/forks/ivansaul/platzi-downloader)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/badge/-Discord-424549?style=social&logo=discord)](https://discord.gg/tDvybtJ7y9)

</div>

---

## Instalación | Actualización

Para [`instalar` | `actualizar` ], ejecuta el siguiente comando en tu terminal:

```console
pip install -U platzi
```

Instala las dependencias de `playwright`:

```console
playwright install chromium
```

> [!IMPORTANT]
> El script utiliza ***`ffmpeg`***, como un subproceso, así que asegúrate de tener instalado y actualizado.

<details>

<summary>Tips & Tricks</summary>

## FFmpeg Instalación

### Ubuntu / Debian

```console
sudo apt install ffmpeg -y
```

### Arch Linux

```console
sudo pacman -S ffmpeg
```

### Windows [[Tutorial]][ffmpeg-youtube]

Puedes descargar la versión de `ffmpeg` para Windows desde [aquí][ffmpeg]. o algún gestor de paquetes como [`Scoop`][scoop] o [`Chocolatey`][chocolatey].

```console
scoop install ffmpeg
```

</details>

## Guía de uso

### Iniciar Sesión

Para iniciar sesión en Platzi, usa el comando login. Esto abrirá una ventana de navegador para autenticarte e iniciar sesión en Platzi.

```console
platzi login
```

### Cookies
Este método se recomienda si tienes problemas de autenticación mediante el método anterior.

```console
platzi set-cookies path/cookies.json
```

<details>

<summary>Tips & Tricks</summary>

## Exportar las cookies

1. Inicia sesión en tu navegador de tu preferencia.
2. Instala alguna extensión como **_`GetCookies`_** o **_`Cookie-Editor`_**
3. Recarga la página.
4. Exporta las cookies en formato `json` desde la extensión.

</details>

### Cerrar Sesión

Para cerrar sesión en Platzi y borrar tu sesión del almacenamiento local, usa el comando `logout`.

```console
platzi logout
```

### Descargar un Curso

> [!IMPORTANT]
> Asegúrate de estar logueado antes de intentar descargar los cursos.

Para descargar un curso de Platzi, usa el comando download seguido de la URL del curso que deseas descargar. La URL puede encontrarse en la barra de direcciones al visualizar la página del curso en Platzi.

También puedes descargar una lista de cursos, proporcionando un archivo de texto con una URL de curso por línea mediante la opción --file (-f). Cada curso será descargado de forma secuencial.

```console
platzi download [URL] [OPTIONS]

OPTIONS:
  -q, --quality     Specifies the video quality (default: 720).
                    Options: [360 | 720 | 1080]

  -w, --overwrite   Overwrite files if they already exist.

  -f, --file        Path to a text file containing one course URL per line.
                    When this option is used, the URL argument is optional.

  --headless        Run the browser in headless mode (default: enabled).
  --no-headless     Use to open a visible browser. Login is performed in a visible browser by default.
```

> [!TIP]
> Para visualizar los comandos disponibles, ejecuta `platzi --help`.
> Para más detalle sobre un comando ejecuta `platzi [COMMAND] --help`.

Ejemplos:

```console
platzi download https://platzi.com/cursos/python
```

```console
platzi download https://platzi.com/cursos/python/ -q 1080
```

```console
platzi download https://platzi.com/cursos/python -w
```

```console
platzi download --file courses.txt
```

### Borrar Caché

Para borrar la caché de Platzi, usa el comando `clear-cache`.

```console
platzi clear-cache
```

> [!TIP]
> Si por algún motivo se cancela la descarga, vuelve a ejecutar `platzi download <url-del-curso>` para retomar la descarga.

<br>

> [!TIP]
> Si obtienes algún error relacionado a `m3u8`o `ts` como por ejemplo; `Error downloading from .ts url` o `Error downloading m3u8`, elimina la carpeta temporal `.tmp` y vuelve a ejecutar el comando.

<br>

> [!TIP]
> Luego de actualizar el script u obtener algún error inesperado se recomienda limpiar la caché antes de volver a intentar descargar el curso. Puedes hacerlo ejecutando el comando `platzi clear-cache`.

## Contribuidores

<a href="https://github.com/ivansaul/vaporz/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=ivansaul/platzi-downloader" />
</a>

## License
Distribuido bajo la Licencia MIT. Consulta el archivo [LICENSE](./LICENSE) para más información.

## **Aviso de Uso**

Este proyecto se realiza con fines exclusivamente educativos y de aprendizaje. El código proporcionado se ofrece "tal cual", sin ninguna garantía de su funcionamiento o idoneidad para ningún propósito específico.

No me hago responsable por cualquier mal uso, daño o consecuencia que pueda surgir del uso de este proyecto. Es responsabilidad del usuario utilizarlo de manera adecuada y dentro de los límites legales y éticos.

[ffmpeg]: https://ffmpeg.org
[chocolatey]: https://community.chocolatey.org
[scoop]: https://scoop.sh
[ffmpeg-youtube]: https://youtu.be/JR36oH35Fgg?si=Gerco7SP8WlZVaKM
