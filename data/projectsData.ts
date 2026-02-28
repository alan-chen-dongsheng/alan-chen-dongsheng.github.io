interface Project {
  title: string
  description: string
  href?: string
  imgSrc?: string
}

const projectsData: Project[] = [
  {
    title: '光照不均图像增强',
    description: `图像增强`,
    imgSrc: '/static/images/google.png',
    href: 'https://github.com/sexjun/Low-light-enhancement',
  },
]

export default projectsData
