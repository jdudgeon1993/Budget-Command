
import {Fragment,memo,useContext,useEffect} from "react"
import {isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_df34074e1a9b1aa9d00de80ec7d0469e = memo(({children}) => {
    const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(RadixThemesBox,{className:"prog-fill",css:({ ["height"] : "100%", ["borderRadius"] : "3px", ["background"] : ((reflex___state____state__cura___state____app_state.total_alloc_val_rx_state_ > reflex___state____state__cura___state____app_state.income_total_rx_state_) ? "#f87171" : "#818cf8"), ["width"] : (reflex___state____state__cura___state____app_state.alloc_pct_rx_state_+"%") })},)
    )
});
