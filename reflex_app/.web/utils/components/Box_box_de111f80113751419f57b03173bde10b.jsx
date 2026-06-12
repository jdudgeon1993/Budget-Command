
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_de111f80113751419f57b03173bde10b = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{css:({ ["width"] : "14px", ["height"] : "14px", ["borderRadius"] : "50%", ["background"] : reflex___state____state__cura___state____app_state.add_bkt_new_cat_color_rx_state_, ["flexShrink"] : "0", ["marginTop"] : "1px" })},)
    )
});
